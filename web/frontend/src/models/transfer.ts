import type {EvidenceViewModel} from "./viewmodel.ts";

export type Decision = "undecided" | "included" | "excluded";

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
}

export type NavigationAction = "first" | "firstUnfilled" | "prev" | "next" | "last" | "unfilled" | "goto";
