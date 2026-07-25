import {render, screen} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {describe, expect, it, vi} from "vitest";
import {SelectionCriteriaForm} from "./SelectionCriteriaForm.tsx";

const evidence = {
    clusterId: 0,
    title: "Study",
    include: true,
    excludeReasons: [],
    keywords: [],
};

describe("selection criteria", () => {
    it("updates exclusion reasons and submits the decision", async () => {
        const user = userEvent.setup();
        const submit = vi.fn().mockResolvedValue(undefined);
        render(<SelectionCriteriaForm evidence={evidence} fileName="study.xlsx" onFormSubmit={submit}/>);

        await user.click(screen.getByLabelText("Does not describe software"));
        expect(screen.getByRole("button", {name: "Exclude"})).toBeInTheDocument();
        await user.click(screen.getByRole("button", {name: "Exclude"}));

        expect(submit).toHaveBeenCalledWith({include: false, excludeReasons: ["not software"]});
    });

    it("removes a selected exclusion reason", async () => {
        const user = userEvent.setup();
        const submit = vi.fn().mockResolvedValue(undefined);
        render(<SelectionCriteriaForm evidence={{...evidence, include: false, excludeReasons: ["not software"]}} fileName="study.xlsx" onFormSubmit={submit}/>);

        await user.click(screen.getByLabelText("Does not describe software"));
        expect(screen.getByRole("button", {name: "Include"})).toBeInTheDocument();
    });
});
