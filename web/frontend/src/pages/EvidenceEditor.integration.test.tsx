import {cleanup, render, screen, waitFor} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {afterEach, beforeEach, describe, expect, it, vi} from "vitest";
import EvidenceEditor from "./EvidenceEditor.tsx";
import {getScreening, updateScreening} from "../api.ts";

vi.mock("../api.ts", () => ({
    getScreening: vi.fn(),
    updateScreening: vi.fn(),
}));

const criteria = {
    review_topic: "entity resolution",
    additional_context: null,
    inclusion_criteria: [{label: "english", description: "Written in English"}],
    exclusion_criteria: [{label: "not software", description: "Does not describe software"}],
};

function screening(index: number, title = `Study ${index}`, withCriteria = true) {
    return {
        recordIndex: index,
        recordCount: 3,
        decision: "undecided" as const,
        exclusionReasons: [],
        evidence: {clusterId: index, title, include: true, excludeReasons: [], keywords: ["ER", "mapping"]},
        previousIndex: index === 0 ? null : index - 1,
        nextIndex: index === 2 ? null : index + 1,
        firstUndecidedIndex: 0,
        nextUndecidedIndex: index === 0 ? 1 : null,
        complete: false,
        selectionCriteria: withCriteria ? criteria : null,
    };
}

describe("EvidenceEditor", () => {
    afterEach(() => cleanup());

    beforeEach(() => {
        vi.mocked(getScreening).mockResolvedValue(screening(0));
        vi.mocked(updateScreening).mockResolvedValue({...screening(1, "Saved study"), nextIndex: null});
    });

    it("loads records, navigates, and renders the provided selection criteria", async () => {
        const user = userEvent.setup();
        render(<EvidenceEditor evidence={screening(0).evidence} fileName="study.xlsx"/>);

        expect(await screen.findByRole("heading", {name: /\[0\].*Study 0/})).toBeInTheDocument();
        expect(screen.getByLabelText("Written in English")).toBeInTheDocument();
        expect(screen.getByLabelText("Does not describe software")).toBeInTheDocument();
        expect(screen.getByText("ER, mapping")).toBeInTheDocument();
        vi.mocked(getScreening).mockResolvedValue(screening(1));
        await user.click(screen.getByTitle("Next item"));
        expect(await screen.findByRole("heading", {name: /\[1\].*Study 1/})).toBeInTheDocument();
    });

    it("navigates to a previous record", async () => {
        const user = userEvent.setup();
        vi.mocked(getScreening).mockResolvedValue(screening(1));
        render(<EvidenceEditor evidence={screening(1).evidence} fileName="study.xlsx"/>);

        await screen.findByRole("heading", {name: /\[1\].*Study 1/});
        vi.mocked(getScreening).mockResolvedValue(screening(0));
        await user.click(screen.getByTitle("Previous item"));
        expect(await screen.findByRole("heading", {name: /\[0\].*Study 0/})).toBeInTheDocument();
    });

    it("jumps to a record by index using the goto input", async () => {
        const user = userEvent.setup();
        render(<EvidenceEditor evidence={screening(0).evidence} fileName="study.xlsx"/>);

        await screen.findByRole("heading", {name: /\[0\].*Study 0/});
        vi.mocked(getScreening).mockResolvedValue(screening(2));
        await user.type(screen.getByPlaceholderText("Go to..."), "2");
        await user.click(screen.getByTitle("Go to item"));
        expect(await screen.findByRole("heading", {name: /\[2\].*Study 2/})).toBeInTheDocument();
    });

    it("navigates to first, last, and undecided records", async () => {
        const user = userEvent.setup();
        vi.mocked(getScreening).mockResolvedValue(screening(1));
        render(<EvidenceEditor evidence={screening(1).evidence} fileName="study.xlsx"/>);

        await screen.findByRole("heading", {name: /\[1\].*Study 1/});
        vi.mocked(getScreening).mockResolvedValue(screening(0));
        await user.click(screen.getByTitle("First item"));
        expect(await screen.findByRole("heading", {name: /\[0\].*Study 0/})).toBeInTheDocument();

        vi.mocked(getScreening).mockResolvedValue(screening(2));
        await user.click(screen.getByTitle("Last item"));
        expect(await screen.findByRole("heading", {name: /\[2\].*Study 2/})).toBeInTheDocument();

        vi.mocked(getScreening).mockResolvedValue(screening(0));
        await user.click(screen.getByTitle("First undecided item"));
        expect(await screen.findByRole("heading", {name: /\[0\].*Study 0/})).toBeInTheDocument();

        vi.mocked(getScreening).mockResolvedValue(screening(1));
        await user.click(screen.getByTitle("Next undecided item"));
        expect(await screen.findByRole("heading", {name: /\[1\].*Study 1/})).toBeInTheDocument();
    });

    it("omits the criteria lists when the workbook has none", async () => {
        vi.mocked(getScreening).mockResolvedValue(screening(0, "Study 0", false));
        render(<EvidenceEditor evidence={screening(0, "Study 0", false).evidence} fileName="study.xlsx"/>);

        await screen.findByRole("heading", {name: /\[0\].*Study 0/});
        expect(screen.queryByText("Inclusion Criteria")).not.toBeInTheDocument();
    });

    it("saves a decision and reports persistence errors", async () => {
        const user = userEvent.setup();
        render(<EvidenceEditor evidence={screening(0).evidence} fileName="study.xlsx"/>);
        await screen.findByRole("heading", {name: /\[0\].*Study 0/});

        await user.click(screen.getByRole("button", {name: "Include"}));
        expect(await screen.findByRole("heading", {name: /\[1\].*Saved study/})).toBeInTheDocument();

        vi.mocked(updateScreening).mockRejectedValue(new Error("failed"));
        await user.click(screen.getByTitle("First item"));
        await user.click(screen.getByRole("button", {name: "Include"}));
        await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Could not save the screening decision."));
    });
});
