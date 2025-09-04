export type ToggleEvidenceStatusRequestBody = {
    id: number;
    toggle: boolean;
    exclude_reasons: string[];
}

export type NavigationAction = "first" | "firstUnfilled" | "prev" | "next" | "last" | "unfilled"