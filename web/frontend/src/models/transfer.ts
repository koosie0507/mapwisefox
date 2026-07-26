import type {EvidenceViewModel} from "./viewmodel.ts";

export type Decision = "undecided" | "included" | "excluded";

export type SelectionCriterion = {
    label: string;
    description: string;
}

export type SelectionConfig = {
    review_topic: string;
    additional_context: string | null;
    inclusion_criteria: SelectionCriterion[];
    exclusion_criteria: SelectionCriterion[];
}

export type ScreeningResponse = {
    recordIndex: number;
    recordCount: number;
    decision: Decision;
    exclusionReasons: string[];
    evidence: EvidenceViewModel;
    previousIndex: number | null;
    nextIndex: number | null;
    firstUndecidedIndex: number | null;
    nextUndecidedIndex: number | null;
    complete: boolean;
    selectionCriteria: SelectionConfig | null;
}

export type NavigationAction = "first" | "firstUnfilled" | "prev" | "next" | "last" | "unfilled" | "goto";
