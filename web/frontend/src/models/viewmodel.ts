export type EvidenceViewModel = {
    clusterId: string | number;
    title: string;
    include: boolean;
    excludeReasons: string[];
    publicationVenue?: string;
    doi?: string;
    doiLink?: string;
    sciHubLink?: string;
    url?: string;
    abstract?: string;
    publishedAt?: string;
    keywords: string[];
}