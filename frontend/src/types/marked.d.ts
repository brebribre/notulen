declare module 'marked' {
  export interface MarkedOptions {
    gfm?: boolean;
    breaks?: boolean;
    sanitize?: boolean;
    [key: string]: any;
  }

  export interface Marked {
    (src: string, options?: MarkedOptions): string;
    setOptions(options: MarkedOptions): void;
  }

  const marked: Marked;
  export { marked };
  export default marked;
} 