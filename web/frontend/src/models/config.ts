export type AppConfig = {
    user: {
        display_name: string | null;
        email: string;
    } | null;
    worksheetName: string;
    expectedColumns: string;
    decisionColumn: string;
    exclusionReasonColumn: string;
};
