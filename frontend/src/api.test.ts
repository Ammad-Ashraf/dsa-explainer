// Unit tests for the helpers the pages share (run with `npm test`).
import { describe, expect, it } from "vitest";
import { algorithmById, type Catalog, cuesToVtt, formatSeconds } from "./api";

describe("cuesToVtt", () => {
  it("writes WebVTT cues the way the backend does", () => {
    const vtt = cuesToVtt([[0, 1.5, "Push seven."], [61.25, 3723.5, "Done --> next"]]);
    expect(vtt.split("\n")).toEqual([
      "WEBVTT", "",
      "1", "00:00:00.000 --> 00:00:01.500", "Push seven.", "",
      "2", "00:01:01.250 --> 01:02:03.500", "Done -> next", "",
    ]);
  });
  it("is just the header when there are no cues", () => {
    expect(cuesToVtt([]).split("\n")).toEqual(["WEBVTT", ""]);
  });
});

describe("formatSeconds", () => {
  it.each([[null, "–"], [undefined, "–"], [4.4, "4 s"], [59.6, "1 min 00 s"], [125, "2 min 05 s"]])("%s -> %s", (input, out) => {
    expect(formatSeconds(input as number | null | undefined)).toBe(out);
  });
});

describe("algorithmById", () => {
  const catalog = { categories: {}, algorithms: [{ id: "bfs", title: "Breadth-first search" }] } as unknown as Catalog;
  it("finds an algorithm, and maps the old name graph to bfs", () => {
    expect(algorithmById(catalog, "bfs")?.title).toBe("Breadth-first search");
    expect(algorithmById(catalog, "graph")?.title).toBe("Breadth-first search");
    expect(algorithmById(catalog, "nope")).toBeUndefined();
  });
});
