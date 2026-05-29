declare module '@deck.gl/core' {
  export interface PickingInfo<T = unknown> {
    object?: T;
  }
}

declare module '@deck.gl/layers' {
  export class ScatterplotLayer<T = unknown> {
    constructor(options: Record<string, unknown>);
  }

  export class TextLayer<T = unknown> {
    constructor(options: Record<string, unknown>);
  }
}

declare module '@deck.gl/aggregation-layers' {
  export class HeatmapLayer<T = unknown> {
    constructor(options: Record<string, unknown>);
  }
}

declare module '@deck.gl/react' {
  const DeckGL: any;
  export default DeckGL;
}
