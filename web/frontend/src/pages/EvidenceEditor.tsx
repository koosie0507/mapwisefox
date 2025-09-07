import {type IncludeStatusArgs, SelectionCriteriaForm} from "../components/SelectionCriteriaForm";
import React, {useRef, useState} from "react";
import {ChevronLeft, ChevronRight, CircleDashed, FastForward, SkipBack, SkipForward} from "lucide-react";
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
    const gotoInputRef = useRef<HTMLInputElement>(null);

    async function navigate(clusterId: string | number, action: NavigationAction) {
        if (action == "firstUnfilled") {
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
        const navAction = (data.complete) ? "next" : "unfilled";
        await navigate(model.clusterId, navAction);
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
                <SelectionCriteriaForm evidence={model} fileName={fileName} onFormSubmit={toggleStatus}/>
            </aside>
            <footer className={styles.bottomPanel}>
                <div className={styles.buttonBar}>
                    <form method="post" action="" onSubmit={evt => evt.preventDefault()}>
                        <div className={styles.gotoGroup}>
                            <input
                                type="text"
                                ref={gotoInputRef}
                                placeholder="Go to…"
                                title="Enter an ID to go to"
                                className={styles.gotoInput}
                                onKeyDown={async (e) => {
                                    if (e.key === 'Enter') {
                                        e.preventDefault();
                                        const v = gotoInputRef.current?.value?.trim();
                                        if (v) await navigate(v, "goto");
                                    }
                                }}
                            />
                            <button
                                type="submit"
                                title="Go to item"
                                className={styles.gotoBtn}
                                onClick={async () => {
                                    const v = gotoInputRef.current?.value?.trim();
                                    if (v) await navigate(v, "goto");
                                }}
                            >
                                <ChevronRight size={18}/>
                            </button>
                        </div>
                        <div className={styles.navGroup}>
                            <button type="submit" title="First item" onClick={async () => await navigate(0, "first")}>
                                <SkipBack size={18}/></button>
                            <button type="submit" title="Previous item"
                                    onClick={async () => await navigate(model.clusterId, "prev")}><ChevronLeft
                                size={18}/>
                            </button>
                            <button type="submit" title="Next item"
                                    onClick={async () => await navigate(model.clusterId, "next")}><ChevronRight
                                size={18}/>
                            </button>
                            <button type="submit" title="Last item" onClick={async () => await navigate(0, "last")}>
                                <SkipForward size={18}/></button>
                            <button type="submit" title="First unfilled item" className={styles.firstGap}
                                    onClick={async () => await navigate(0, "firstUnfilled")}><CircleDashed size={18}/>
                            </button>
                            <button type="submit" title="Next unfilled item" className={styles.nextUndecided}
                                    onClick={async () => await navigate(model.clusterId, "unfilled")}><FastForward
                                size={18}/></button>
                        </div>
                    </form>
                </div>
            </footer>
        </div>
    )
}
