import {render, screen, waitFor} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {beforeEach, describe, expect, it, vi} from "vitest";
import EvidenceEditor from "./EvidenceEditor.tsx";
import {getScreening, updateScreening} from "../api.ts";

vi.mock("../api.ts", () => ({
    getScreening: vi.fn(),
    updateScreening: vi.fn(),
}));

function screening(index: number, title = `Study ${index}`) {
    return {
        recordIndex: index,
        recordCount: 3,
        decision: "undecided" as const,
        exclusionReasons: [],
        evidence: {clusterId: index, title, include: true, excludeReasons: [], keywords: ["ER"]},
        previousIndex: index === 0 ? null : index - 1,
        nextIndex: index === 2 ? null : index + 1,
        firstUndecidedIndex: 0,
        nextUndecidedIndex: index === 0 ? 1 : null,
        complete: false,
    };
}

describe("EvidenceEditor", () => {
    beforeEach(() => {
        vi.mocked(getScreening).mockResolvedValue(screening(0));
        vi.mocked(updateScreening).mockResolvedValue({...screening(1, "Saved study"), nextIndex: null});
    });

    it("loads records and navigates to the next item", async () => {
        const user = userEvent.setup();
        render(<EvidenceEditor evidence={screening(0).evidence} fileName="study.xlsx"/>);

        expect(await screen.findByRole("heading", {name: "[0] Study 0"})).toBeInTheDocument();
        vi.mocked(getScreening).mockResolvedValue(screening(1));
        await user.click(screen.getByTitle("Next item"));
        expect(await screen.findByRole("heading", {name: "[1] Study 1"})).toBeInTheDocument();
    });

    it("saves a decision and reports persistence errors", async () => {
        const user = userEvent.setup();
        render(<EvidenceEditor evidence={screening(0).evidence} fileName="study.xlsx"/>);
        await screen.findByRole("heading", {name: "[0] Study 0"});

        await user.click(screen.getByRole("button", {name: "Include"}));
        expect(await screen.findByRole("heading", {name: "[1] Saved study"})).toBeInTheDocument();

        vi.mocked(updateScreening).mockRejectedValue(new Error("failed"));
        await user.click(screen.getByTitle("First item"));
        await user.click(screen.getByRole("button", {name: "Include"}));
        await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Could not save the screening decision."));
    });
});
