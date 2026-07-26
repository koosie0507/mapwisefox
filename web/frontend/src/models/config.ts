export type AppConfig = {
    user: {
        display_name: string | null;
        email: string;
    } | null;
    supportedFields: Array<{
        name: string;
        mandatory: boolean;
    }>;
    decisionColumn: string;
    exclusionReasonColumn: string;
};
