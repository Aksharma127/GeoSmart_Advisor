module GeoSmartCore

using Dates
using DataFrames
using Distances
using HTTP
using Interpolations
using JSON3
using LinearAlgebra
using Statistics
using StaticArrays

export LocationFeatures, compute_viability_score, viability_loss, run_spatial_simulation

const EARTH_RADIUS_M = 6_371_000.0
const MIN_ZONE_SEPARATION_M = 300.0
const VERSION = "1.0.0"

mutable struct ScoreContext
    zone_ids::Vector{Int}
    base_scores::Vector{Float64}
    adjusted_scores::Vector{Float64}
    breakdowns::Vector{Dict{String, Any}}
end

struct LocationFeatures
    lat::Float64
    lon::Float64
    demographic_density::Float64
    median_income::Float64
    infra_proximity_score::Float64
    competitor_count::Int
    foot_traffic_proxy::Float64
    zoning_score::Float64
    market_gap_score::Float64
end

module ViabilityEngine

import ..GeoSmartCore: LocationFeatures
using LinearAlgebra
using Statistics

export LocationFeatures, compute_viability_score, viability_loss, feature_breakdown

const DEMOGRAPHIC_REFERENCE = 20_000.0
const INCOME_REFERENCE = 100_000.0
const COMPETITOR_REFERENCE = 15.0

clamp01(value::Real) = clamp(Float64(value), 0.0, 1.0)

normalize_density(value::Real) = clamp(log1p(max(Float64(value), 0.0)) / log1p(DEMOGRAPHIC_REFERENCE), 0.0, 1.0)
normalize_income(value::Real) = clamp(log1p(max(Float64(value), 0.0)) / log1p(INCOME_REFERENCE), 0.0, 1.0)
normalize_infra(value::Real) = clamp01(value)
normalize_competitor_inverse(value::Integer) = exp(-max(Float64(value), 0.0) / COMPETITOR_REFERENCE)
normalize_traffic(value::Real) = clamp01(value)
normalize_zoning(value::Real) = clamp01(value)
normalize_market_gap(value::Real) = clamp01(value)

function feature_breakdown(f::LocationFeatures)::Dict{String, Float64}
    demographic = normalize_density(f.demographic_density)
    income = normalize_income(f.median_income)
    infra = normalize_infra(f.infra_proximity_score)
    competitor = normalize_competitor_inverse(f.competitor_count)
    foot_traffic = normalize_traffic(f.foot_traffic_proxy)
    zoning = normalize_zoning(f.zoning_score)
    market_gap = normalize_market_gap(f.market_gap_score)

    raw = 0.20 * demographic + 0.25 * income + 0.15 * infra + 0.15 * competitor + 0.10 * foot_traffic + 0.10 * zoning + 0.05 * market_gap
    score = 100.0 / (1.0 + exp(-6.0 * (raw - 0.5)))

    return Dict(
        "demographic_normalized" => demographic,
        "income_normalized" => income,
        "infra_normalized" => infra,
        "competitor_inverse_normalized" => competitor,
        "foot_traffic_normalized" => foot_traffic,
        "zoning_normalized" => zoning,
        "market_gap_normalized" => market_gap,
        "demographic_weighted" => 0.20 * demographic,
        "income_weighted" => 0.25 * income,
        "infra_weighted" => 0.15 * infra,
        "competitor_weighted" => 0.15 * competitor,
        "foot_traffic_weighted" => 0.10 * foot_traffic,
        "zoning_weighted" => 0.10 * zoning,
        "market_gap_weighted" => 0.05 * market_gap,
        "raw" => raw,
        "score" => score,
    )
end

function compute_viability_score(f::LocationFeatures)::Float64
    breakdown = feature_breakdown(f)
    return clamp(Float64(breakdown["score"]), 0.0, 100.0)
end

function viability_loss(predicted, actual)
    predicted_value = Float64(predicted)
    actual_value = Float64(actual)
    if predicted_value > actual_value
        return 1.5 * (predicted_value - actual_value)^2
    end
    return 0.8 * (actual_value - predicted_value)^2
end

end

module SpatialMatrix

import ..GeoSmartCore: EARTH_RADIUS_M, LocationFeatures, MIN_ZONE_SEPARATION_M
import ..GeoSmartCore.ViabilityEngine: compute_viability_score
using Distances
using LinearAlgebra
using StaticArrays

export run_spatial_simulation, build_zone_assignments, distance_matrix_haversine, zone_competition_penalty

const DISTANCE_METRIC = Haversine(EARTH_RADIUS_M)

function candidate_point(candidate::LocationFeatures)
    return SVector{2, Float64}(candidate.lat, candidate.lon)
end

function distance_matrix_haversine(candidates::Vector{LocationFeatures})::Matrix{Float64}
    count = length(candidates)
    matrix = Matrix{Float64}(undef, count, count)
    points = map(candidate_point, candidates)
    for row in 1:count
        matrix[row, row] = 0.0
        for col in (row + 1):count
            distance = evaluate(DISTANCE_METRIC, points[row], points[col])
            matrix[row, col] = distance
            matrix[col, row] = distance
        end
    end
    return matrix
end

function build_zone_assignments(candidates::Vector{LocationFeatures}, base_scores::Vector{Float64}, distance_matrix::Matrix{Float64})
    count = length(candidates)
    ordering = sortperm(base_scores, rev = true)
    zone_ids = zeros(Int, count)
    representatives = Int[]
    zone_of_representative = Int[]

    for index in ordering
        assigned_zone = 0
        closest_distance = Inf
        closest_zone_index = 0

        for (position, representative_index) in enumerate(representatives)
            distance = distance_matrix[index, representative_index]
            if distance <= MIN_ZONE_SEPARATION_M && distance < closest_distance
                closest_distance = distance
                closest_zone_index = position
            end
        end

        if closest_zone_index == 0
            push!(representatives, index)
            push!(zone_of_representative, length(zone_of_representative) + 1)
            assigned_zone = zone_of_representative[end]
        else
            assigned_zone = zone_of_representative[closest_zone_index]
        end

        zone_ids[index] = assigned_zone
    end

    for index in 1:count
        if zone_ids[index] == 0
            closest_zone = 1
            closest_distance = Inf
            for (position, representative_index) in enumerate(representatives)
                distance = distance_matrix[index, representative_index]
                if distance < closest_distance
                    closest_distance = distance
                    closest_zone = zone_of_representative[position]
                end
            end
            zone_ids[index] = closest_zone
        end
    end

    return zone_ids
end

function zone_competition_penalty(zone_indices::Vector{Int}, base_scores::Vector{Float64}, distance_matrix::Matrix{Float64})::Float64
    if length(zone_indices) <= 1
        return 0.0
    end

    zone_scores = base_scores[zone_indices]
    top_score = maximum(zone_scores)
    active_indices = [index for index in zone_indices if base_scores[index] >= top_score - 10.0]

    if length(active_indices) <= 1
        return 0.0
    end

    close_pairs = 0.0
    total_pairs = 0.0
    for left in 1:length(active_indices)
        for right in (left + 1):length(active_indices)
            total_pairs += 1.0
            distance = distance_matrix[active_indices[left], active_indices[right]]
            close_pairs += exp(-distance / MIN_ZONE_SEPARATION_M)
        end
    end

    density_penalty = 4.0 * (length(zone_indices) - 1)
    clustering_penalty = total_pairs == 0.0 ? 0.0 : 8.0 * (close_pairs / total_pairs)
    return clamp(density_penalty + clustering_penalty, 0.0, 20.0)
end

function run_spatial_simulation(candidates::Vector{LocationFeatures})
    if isempty(candidates)
        return Tuple{LocationFeatures, Float64}[]
    end

    base_scores = [compute_viability_score(candidate) for candidate in candidates]
    distance_matrix = distance_matrix_haversine(candidates)
    zone_ids = build_zone_assignments(candidates, base_scores, distance_matrix)
    adjusted_scores = similar(base_scores)

    for zone_id in unique(zone_ids)
        zone_indices = findall(==(zone_id), zone_ids)
        penalty = zone_competition_penalty(zone_indices, base_scores, distance_matrix)
        for index in zone_indices
            adjusted_scores[index] = clamp(base_scores[index] - penalty, 0.0, 100.0)
        end
    end

    return [(candidates[index], adjusted_scores[index]) for index in eachindex(candidates)]
end

end

module HTTPServer

import ..GeoSmartCore: LocationFeatures, VERSION
import ..GeoSmartCore.SpatialMatrix: build_zone_assignments, distance_matrix_haversine, run_spatial_simulation
import ..GeoSmartCore.ViabilityEngine: compute_viability_score, feature_breakdown
using Dates
using HTTP
using JSON3
using Sockets

export start_server

function json_response(payload; status::Int = 200)
    return HTTP.Response(status, ["Content-Type" => "application/json"], JSON3.write(payload))
end

function error_response(message::AbstractString; status::Int = 500)
    return json_response(Dict("error" => String(message)); status = status)
end

function read_body_text(request::HTTP.Request)
    return String(request.body)
end

function parse_location_feature(entry)
    return LocationFeatures(
        Float64(entry["lat"]),
        Float64(entry["lon"]),
        Float64(entry["demographic_density"]),
        Float64(entry["median_income"]),
        Float64(entry["infra_proximity_score"]),
        Int(entry["competitor_count"]),
        Float64(entry["foot_traffic_proxy"]),
        Float64(entry["zoning_score"]),
        Float64(entry["market_gap_score"]),
    )
end

function score_payload(candidates::Vector{LocationFeatures})
    scores = [compute_viability_score(candidate) for candidate in candidates]
    distance_matrix = distance_matrix_haversine(candidates)
    zone_ids = build_zone_assignments(candidates, scores, distance_matrix)

    payload = Vector{Dict{String, Any}}(undef, length(candidates))
    for index in eachindex(candidates)
        payload[index] = Dict(
            "lat" => candidates[index].lat,
            "lon" => candidates[index].lon,
            "score" => scores[index],
            "zone_id" => zone_ids[index],
            "breakdown" => feature_breakdown(candidates[index]),
        )
    end
    return payload
end

function simulate_payload(candidates::Vector{LocationFeatures}, top_n::Int)
    scored = run_spatial_simulation(candidates)
    zone_best = Dict{Int, Tuple{LocationFeatures, Float64, Dict{String, Any}}}()
    base_scores = [compute_viability_score(candidate) for candidate in candidates]
    distance_matrix = distance_matrix_haversine(candidates)
    zone_ids = build_zone_assignments(candidates, base_scores, distance_matrix)

    for (index, (candidate, score)) in enumerate(scored)
        zone_id = zone_ids[index]
        breakdown = feature_breakdown(candidate)
        breakdown["adjusted_score"] = score
        if !haskey(zone_best, zone_id) || score > zone_best[zone_id][2]
            zone_best[zone_id] = (candidate, score, breakdown)
        end
    end

    ranked = sort(collect(zone_best), by = entry -> entry[2][2], rev = true)
    selected = first(ranked, min(top_n, length(ranked)))
    return [Dict(
        "lat" => candidate.lat,
        "lon" => candidate.lon,
        "score" => score,
        "zone_id" => zone_id,
        "breakdown" => breakdown,
    ) for (zone_id, (candidate, score, breakdown)) in selected]
end

function route_handler(request::HTTP.Request)
    started_at = time_ns()
    status_code = 200
    response = nothing
    route = string(request.method) * " " * string(request.target)

    try
        path = string(HTTP.URI(string(request.target)).path)
        method = uppercase(string(request.method))
        if method == "GET" && path == "/health"
            response = json_response(Dict("status" => "ok", "version" => VERSION))
        elseif method == "POST" && path == "/score"
            body_text = read_body_text(request)
            candidates, _ = parse_candidates_array(body_text)
            response = json_response(score_payload(candidates))
        elseif method == "POST" && path == "/simulate"
            body_text = read_body_text(request)
            payload = JSON3.read(body_text, Dict{String, Any})
            raw_candidates = payload["candidates"]
            if !(raw_candidates isa AbstractVector)
                error("candidates must be an array")
            end
            top_n = haskey(payload, "top_n") ? Int(payload["top_n"]) : 10
            candidates = [parse_location_feature(entry) for entry in raw_candidates]
            response = json_response(simulate_payload(candidates, top_n))
        else
            status_code = 404
            response = error_response("route not found"; status = status_code)
        end
    catch err
        status_code = 500
        response = error_response(sprint(showerror, err); status = status_code)
    finally
        elapsed_ms = (time_ns() - started_at) / 1e6
        timestamp = Dates.format(Dates.now(), dateformat"yyyy-mm-ddTHH:MM:SS.sss")
        println("[$timestamp] $route status=$status_code latency_ms=$(round(elapsed_ms, digits = 2))")
    end

    return response
end

function parse_candidates_array(body_text::AbstractString)
    payload = JSON3.read(body_text)
    raw_candidates = if payload isa AbstractVector
        payload
    elseif haskey(payload, :candidates)
        payload[:candidates]
    elseif haskey(payload, "candidates")
        payload["candidates"]
    else
        error("request body must be a candidates array or an object with candidates")
    end

    if !(raw_candidates isa AbstractVector)
        error("candidates must be an array")
    end
    candidates = LocationFeatures[]
    for entry in raw_candidates
        push!(candidates, parse_location_feature(entry))
    end
    return candidates, payload
end

function start_server(; host = "0.0.0.0", port = 8001)
    println("GeoSmartCore listening on $(host):$(port)")
    HTTP.serve(route_handler, host, port; verbose = false)
end

end

end

using .GeoSmartCore.HTTPServer

if abspath(PROGRAM_FILE) == @__FILE__
    HTTPServer.start_server()
end
