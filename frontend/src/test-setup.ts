import "@testing-library/jest-dom/vitest";

// Polyfill ResizeObserver for radix-ui components
class ResizeObserverMock {
  observe() {}
  unobserve() {}
  disconnect() {}
}
globalThis.ResizeObserver = ResizeObserverMock;

// Polyfill scrollIntoView for jsdom
Element.prototype.scrollIntoView = function () {};

// Polyfill matchMedia for responsive components
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});
