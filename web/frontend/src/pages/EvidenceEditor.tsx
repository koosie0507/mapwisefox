import SelectionCriteriaForm from "../components/SelectionCriteriaForm";
import React from "react";

type EvidenceRecord = {
    clusterId: string | number;
    include: "include" | "exclude" | boolean;
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

type EvidenceProps = {
    evidence: EvidenceRecord
    fileName: string
};

function safeUrl(url?: string): string {
    return url || "#"
}

function SafeLink({url, text, label, style}: {
    url?: string,
    text?: string,
    label?: string,
    style?: React.CSSProperties
}) {
    if (label !== undefined && label !== null) {
        const spanStyle = style || {fontSize: "9px", margin: "2px"}
        return (
            <span style={spanStyle}>
                <b>{label}</b>&nbsp;
                <a href={safeUrl(url)} target="_blank">{text}</a>
            </span>
        )
    }
    return <a href={safeUrl(url)} target="_blank">{text}</a>;
}

export default function EvidenceEditor({evidence, fileName}: EvidenceProps) {
    const doiText = evidence.doi || "n/a"
    const dateText = (evidence.publishedAt || "n/a").toString()
    return (
        <div>
            <main className="main-container">
                <div>
                    <div className="article-info">
                        <div className="source-container">
                            <SafeLink url={evidence.url} text={evidence.publicationVenue} label="Source:"
                                      style={{fontSize: "12px", margin: "2px"}}/>
                            <SafeLink url={evidence.doiLink} text={doiText} label="DOI:"/>
                            <SafeLink url={evidence.sciHubLink} text={doiText} label="SciHub:"/>
                        </div>
                        <small style={{fontSize: "9px", margin: "2px"}}>
                            <b>Date Published:</b>&nbsp;
                            {dateText}
                        </small>
                    </div>
                    <b className="abstract-label">Abstract</b>
                    <div className="scrollbox">
                        {evidence.abstract}
                    </div>
                    <p className="keywords">
                        <strong>Keywords:</strong>
                        {evidence.keywords}
                    </p>
                </div>
                <SelectionCriteriaForm evidenceId={evidence.clusterId}
                                       fileName={fileName}
                                       include={evidence.include}
                                       exclusionCriteria={evidence.excludeReasons}
                />
            </main>
            <footer className="footer-container">
                <div className="button-bar">
                    <form method="post" action={`/evidence/${fileName}/process-form`}>
                        <input type="hidden" name="id" value={evidence.clusterId}/>
                        <button type="submit" name="action" value="prev">Previous</button>
                        <button type="submit" name="action" value="next">Next
                        </button>
                        <span className="goto-group">
                            <input type="number" name="index" value={evidence.clusterId} style={{width: "4em"}}/>
                            <button type="submit" name="action" value="goto">Go To</button>
                        </span>
                        <button type="submit" name="action" value="next-unfilled">First Unfilled</button>
                    </form>
                </div>
            </footer>
        </div>
    )
}
