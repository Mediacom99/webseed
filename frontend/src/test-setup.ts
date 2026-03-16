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
