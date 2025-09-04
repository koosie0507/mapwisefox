import {type FormEvent, useEffect, useState} from "react";
import InclusionStatus from "./InclusionStatus.tsx";
import {type StatusChangedArgs, SelectionCriterion} from "./SelectionCriterion.tsx";
import "../styles/form.css";
import type {EvidenceViewModel} from "../models/viewmodel.ts";

export type IncludeStatusArgs = {
    include: boolean,
    excludeReasons: string[]
}

type SelectionCriteriaFormProps = {
    evidence: EvidenceViewModel
    fileName: string
    onFormSubmit: (args: IncludeStatusArgs) => Promise<void>;
}

export function SelectionCriteriaForm({evidence, onFormSubmit}: SelectionCriteriaFormProps) {
    const [include, setInclude] = useState(evidence.include)
    const [excludeReasons, setExcludeReasons] = useState<string[]>(evidence.excludeReasons)

    useEffect(() => {
        setInclude(evidence.include);
        setExcludeReasons(evidence.excludeReasons ?? []);
    }, [evidence]);

    function manipulateExcludeReasons(include: boolean, excludeReason: string) {
        const buf = Object.assign([], excludeReasons);
        const idx = buf.indexOf(excludeReason)
        if (include) {
            if (idx >= 0) {
                buf.splice(idx, 1);
            }
        } else {
            if (idx < 0) {
                buf.push(excludeReason);
            }
        }
        setExcludeReasons(buf)
        setInclude(buf.length == 0)
    }

    async function handleIncludeStatusChanged({newValue, excludeReason}: StatusChangedArgs) {
        manipulateExcludeReasons(newValue, excludeReason);
    }

    async function submitData(evt: FormEvent<HTMLFormElement>) {
        evt.preventDefault();
        await onFormSubmit({include, excludeReasons});
    }

    return (
        <form className="criteria-form" onSubmit={submitData}>
            <InclusionStatus include={include} excludeReasons={excludeReasons} />
            <h3>Inclusion Criteria</h3>
            <ul>
                <SelectionCriterion evidence={evidence} criterionId="include_0"
                           criterionType="include"
                           excludeReason="not er"
                           onStatusChanged={handleIncludeStatusChanged}>
                    is about entity resolution (or a derivative)
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="include_1"
                           criterionType="include"
                           excludeReason="not published 2010-2025"
                           onStatusChanged={handleIncludeStatusChanged}>
                    01.01.2010 &dash; 15.06.2025
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="include_2"
                           criterionType="include"
                           excludeReason="not english"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Written in English
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="include_3"
                           criterionType="include"
                           excludeReason="not accessible"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Access to full text available
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="include_4"
                           criterionType="include"
                           excludeReason="not most comprehensive system description"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Most comprehensive description of system according to authors
                </SelectionCriterion>
            </ul>
            <h3>Exclusion Criteria</h3>
            <ul>
                <SelectionCriterion evidence={evidence} criterionId="exclude_1"
                           criterionType="exclude"
                           excludeReason="not peer reviewed"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Does not have peer-reviewed paper
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="exclude_2"
                           criterionType="exclude"
                           excludeReason="not software"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Does not describe software
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="exclude_3"
                           criterionType="exclude"
                           excludeReason="not e2e"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Focused on a component of ER without mentioning the end-to-end ER process
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="exclude_4"
                           criterionType="exclude"
                           excludeReason="not generic er"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Does not describe ER, but an application of ER
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="exclude_5"
                           criterionType="exclude"
                           excludeReason="not system"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Describes a technique, method or experiment instead of a full-blown system
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="exclude_6"
                           criterionType="exclude"
                           excludeReason="secondary study"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Is a secondary study (review, mapping study, etc.)
                </SelectionCriterion>
                <SelectionCriterion evidence={evidence} criterionId="exclude_7"
                           criterionType="exclude"
                           excludeReason="low quality"
                           onStatusChanged={handleIncludeStatusChanged}>
                    Is low quality(<i>only after QA</i>)
                </SelectionCriterion>
            </ul>
        </form>
    )
}