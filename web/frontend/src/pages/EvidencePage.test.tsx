import {render, screen, waitFor} from "@testing-library/react";
import {MemoryRouter, Route, Routes} from "react-router-dom";
import {beforeEach, describe, expect, it, vi} from "vitest";
import EvidencePage from "./EvidencePage.tsx";

vi.mock("../api.ts", () => ({
    getScreening: vi.fn(),
}));

import {getScreening} from "../api.ts";

function screening(index: number, firstUndecided: number | null) {
    return {
        recordIndex: index,
        recordCount: 3,
        decision: "undecided" as const,
        exclusionReasons: [],
        evidence: {clusterId: index, title: `Study ${index}`, include: true, excludeReasons: [], keywords: []},
        previousIndex: null,
        nextIndex: null,
        firstUndecidedIndex: firstUndecided,
        nextUndecidedIndex: null,
        complete: false,
        selectionCriteria: null,
    };
}

function renderPage(path: string) {
    return render(
        <MemoryRouter initialEntries={[path]}>
            <Routes>
                <Route path="/evidence/:fileName" element={<EvidencePage/>}/>
            </Routes>
        </MemoryRouter>
    );
}

describe("EvidencePage", () => {
    beforeEach(() => vi.mocked(getScreening).mockReset());

    it("redirects to the first undecided index when no index is given", async () => {
        vi.mocked(getScreening)
            .mockResolvedValueOnce(screening(0, 2))
            .mockResolvedValueOnce(screening(2, 2))
            .mockResolvedValue(screening(2, 2));

        renderPage("/evidence/studies.xlsx");

        expect(await screen.findByRole("heading", {name: /\[2\].*Study 2/})).toBeInTheDocument();
        expect(getScreening).toHaveBeenCalledWith(expect.any(String), 2);
    });

    it("uses the given index when it is provided", async () => {
        vi.mocked(getScreening).mockResolvedValue(screening(1, null));

        renderPage("/evidence/studies.xlsx?index=1");

        expect(await screen.findByRole("heading", {name: /\[1\].*Study 1/})).toBeInTheDocument();
        expect(getScreening).toHaveBeenCalledWith(expect.any(String), 1);
    });

    it("shows an error for an invalid index query parameter", async () => {
        renderPage("/evidence/studies.xlsx?index=abc");

        expect(await screen.findByRole("alert")).toHaveTextContent("Could not load that screening record.");
        expect(getScreening).not.toHaveBeenCalled();
    });

    it("shows an error when the screening fetch fails", async () => {
        vi.mocked(getScreening).mockRejectedValueOnce(new Error("offline")).mockResolvedValue(screening(0, null));

        renderPage("/evidence/studies.xlsx?index=0");

        await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Could not load that screening record."));
    });
});