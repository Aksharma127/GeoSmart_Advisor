FROM julia:1.10

WORKDIR /app

COPY Project.toml ./
RUN julia --project=. -e "using Pkg; Pkg.instantiate()"

COPY src ./src

EXPOSE 8001

CMD ["julia", "--project=.", "src/GeoSmartCore.jl"]
