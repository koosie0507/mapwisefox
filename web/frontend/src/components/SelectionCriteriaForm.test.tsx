import {render, screen} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {describe, expect, it, vi} from "vitest";
import {SelectionCriteriaForm} from "./SelectionCriteriaForm.tsx";
import type {SelectionConfig} from "../models/transfer.ts";

const evidence = {
    clusterId: 0,
    title: "Study",
    include: true,
    excludeReasons: [],
    keywords: [],
};

const criteria: SelectionConfig = {
    review_topic: "entity resolution",
    additional_context: null,
    inclusion_criteria: [
        {label: "english", description: "Written in English"},
        {label: "er", description: "Is about entity resolution"},
    ],
    exclusion_criteria: [
        {label: "not software", description: "Does not describe software"},
        {label: "secondary study", description: "Is a secondary study"},
    ],
};

describe("selection criteria", () => {
    it("renders the provided criteria descriptions", () => {
        render(<SelectionCriteriaForm evidence={evidence} fileName="study.xlsx" criteria={criteria} onFormSubmit={vi.fn()}/>);

        expect(screen.getByLabelText("Written in English")).toBeInTheDocument();
        expect(screen.getByLabelText("Does not describe software")).toBeInTheDocument();
    });

    it("updates exclusion reasons and submits the decision", async () => {
        const user = userEvent.setup();
        const submit = vi.fn().mockResolvedValue(undefined);
        render(<SelectionCriteriaForm evidence={evidence} fileName="study.xlsx" criteria={criteria} onFormSubmit={submit}/>);

        await user.click(screen.getByLabelText("Does not describe software"));
        expect(screen.getByRole("button", {name: "Exclude"})).toBeInTheDocument();
        await user.click(screen.getByRole("button", {name: "Exclude"}));

        expect(submit).toHaveBeenCalledWith({include: false, excludeReasons: ["not software"]});
    });

    it("removes a selected exclusion reason", async () => {
        const user = userEvent.setup();
        const submit = vi.fn().mockResolvedValue(undefined);
        render(<SelectionCriteriaForm evidence={{...evidence, include: false, excludeReasons: ["not software"]}} fileName="study.xlsx" criteria={criteria} onFormSubmit={submit}/>);

        await user.click(screen.getByLabelText("Does not describe software"));
        expect(screen.getByRole("button", {name: "Include"})).toBeInTheDocument();
    });

    it("renders no criteria lists when criteria is null", () => {
        render(<SelectionCriteriaForm evidence={evidence} fileName="study.xlsx" criteria={null} onFormSubmit={vi.fn()}/>);

        expect(screen.queryByText("Inclusion Criteria")).not.toBeInTheDocument();
        expect(screen.queryByText("Exclusion Criteria")).not.toBeInTheDocument();
    });

    it("unchecking an inclusion criterion excludes the record", async () => {
        const user = userEvent.setup();
        const submit = vi.fn().mockResolvedValue(undefined);
        render(<SelectionCriteriaForm evidence={evidence} fileName="study.xlsx" criteria={criteria} onFormSubmit={submit}/>);

        await user.click(screen.getByLabelText("Written in English"));
        await user.click(screen.getByRole("button", {name: "Exclude"}));

        expect(submit).toHaveBeenCalledWith({include: false, excludeReasons: ["english"]});
    });
});