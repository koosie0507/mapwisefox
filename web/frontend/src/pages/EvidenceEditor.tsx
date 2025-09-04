import {type IncludeStatusArgs, SelectionCriteriaForm} from "../components/SelectionCriteriaForm";
import React, {useState} from "react";
import {SkipBack, ChevronLeft, ChevronRight, SkipForward, FastForward, CircleDashed} from "lucide-react";
import styles from "./EvidenceEditor.module.css";
import type {NavigationAction} from "../models/transfer.ts";
import type {EvidenceViewModel} from "../models/viewmodel.ts";

type EvidenceProps = {
    evidence: EvidenceViewModel
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
    const navigateEndpoint = `/evidence/${fileName}/navigate`
    const toggleStatusEndpoint = `/evidence/${fileName}/save`
    const [model, setModel] = useState<EvidenceViewModel>(evidence)

    async function navigate(action: NavigationAction) {
        let clusterId = model.clusterId
        if (action == "firstUnfilled") {
            clusterId = 0
            action = "unfilled"
        }
        const res = await fetch(navigateEndpoint, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                clusterId: clusterId,
                action: action,
            })
        })
        if (res.status >= 400) {
            console.error(res.statusText)
            return;
        }
        const data = await res.json()
        setModel(data.evidence)
    }

    async function toggleStatus({include, excludeReasons}: IncludeStatusArgs) {
        const res = await fetch(toggleStatusEndpoint, {
            method: "PATCH",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({clusterId: model.clusterId, include, excludeReasons})
        })
        if (res.status >= 400) {
            return;
        }
        const data = await res.json()
        if (data.changed) {
            setModel(data.evidence)
        }
        await navigate("unfilled")
    }

    return (
        <div className={styles.layout}>
            <main className={styles.mainContent}>
                <h1>[{model.clusterId}]&nbsp;{model.title}</h1>
                <div className="article-info">
                    <div className="source-container">
                        <SafeLink url={model.url} text={model.publicationVenue} label="Source:"
                                  style={{fontSize: "12px", margin: "2px"}}/>
                        <SafeLink url={model.doiLink} text={doiText} label="DOI:"/>
                        <SafeLink url={model.sciHubLink} text={doiText} label="SciHub:"/>
                    </div>
                    <small style={{fontSize: "9px", margin: "2px"}}>
                        <b>Date Published:</b>&nbsp;
                        {dateText}
                    </small>
                </div>
                <b className="abstract-label">Abstract</b>
                <div className={styles.scrollbox}>
                    {model.abstract}
                </div>
                <p className="keywords">
                    <strong>Keywords:</strong>
                    {model.keywords}
                </p>
            </main>
            <aside className={`${styles.rightSidebar} sidebar`}>
                <SelectionCriteriaForm evidence={model} fileName={fileName} onFormSubmit={toggleStatus} />
            </aside>
            <footer className={styles.bottomPanel}>
                <div className={styles.buttonBar}>
                    <form method="post" action="" onSubmit={evt=>evt.preventDefault()}>
                        <button type="submit" title="First item" onClick={async () => await navigate("first")}><SkipBack size={18} /></button>
                        <button type="submit" title="Previous item" onClick={async () => await navigate("prev")}><ChevronLeft size={18} /></button>
                        <button type="submit" title="Next item" onClick={async () => await navigate("next")}><ChevronRight size={18} /></button>
                        <button type="submit" title="Last item" onClick={async () => await navigate("last")}><SkipForward size={18} /></button>
                        <button type="submit" title="First unfilled item" className={styles.firstGap} onClick={async () => await navigate("firstUnfilled")}><CircleDashed size={18} /></button>
                        <button type="submit" title="Next unfilled item" className={styles.nextUndecided} onClick={async () => await navigate("unfilled")}><FastForward size={18} /></button>
                    </form>
                </div>
            </footer>
        </div>
    )
}
