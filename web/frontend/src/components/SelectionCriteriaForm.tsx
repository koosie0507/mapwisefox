import React from "react";
import InclusionStatus from "./InclusionStatus.tsx";
import Criterion from "./SelectionCriterion.tsx";
import "../styles/form.css";

type SelectionCriteriaFormProps = {
    include: "include" | "exclude" | boolean
    exclusionCriteria: Array<string>
    evidenceId: number | string
    fileName: string
}

export default function SelectionCriteriaForm(props: SelectionCriteriaFormProps) {
    const [include, setInclude] = React.useState(props.include);
    const [exclusionReasons, setExclusionReasons] = React.useState(props.exclusionCriteria);

    // @ts-expect-error TS7031
    function handleToggle({status, remainingExclusions}) {
        setInclude(status)
        setExclusionReasons(remainingExclusions)
    }

    return (
        <aside className="sidebar" id="selection-criteria">
            <form className="criteria-form" onSubmit={(e) => e.preventDefault()}>
                <InclusionStatus status={include} exclusionReasons={exclusionReasons}/>
                <h3>Inclusion Criteria</h3>
                <ul>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="include_0"
                               criterionType="include"
                               excludeReason="not er"
                               onToggleCompleted={handleToggle}>
                        is about entity resolution (or a derivative)
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="include_1"
                               criterionType="include"
                               excludeReason="not published 2010-2025"
                               onToggleCompleted={handleToggle}>
                        01.01.2010 &dash; 15.06.2025
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="include_2"
                               criterionType="include"
                               excludeReason="not english"
                               onToggleCompleted={handleToggle}>
                        Written in English
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="include_3"
                               criterionType="include"
                               excludeReason="not accessible"
                               onToggleCompleted={handleToggle}>
                        Access to full text available
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="include_4"
                               criterionType="include"
                               excludeReason="not most comprehensive system description"
                               onToggleCompleted={handleToggle}>
                        Most comprehensive description of system according to authors
                    </Criterion>
                </ul>
                <h3>Exclusion Criteria</h3>
                <ul>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="exclude_1"
                               criterionType="exclude"
                               excludeReason="not peer reviewed"
                               onToggleCompleted={handleToggle}>
                        Does not have peer-reviewed paper
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="exclude_2"
                               criterionType="exclude"
                               excludeReason="not software"
                               onToggleCompleted={handleToggle}>
                        Does not describe software
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="exclude_3"
                               criterionType="exclude"
                               excludeReason="not e2e"
                               onToggleCompleted={handleToggle}>
                        Focused on a component of ER without mentioning the end-to-end ER process
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="exclude_4"
                               criterionType="exclude"
                               excludeReason="not generic er"
                               onToggleCompleted={handleToggle}>
                        Does not describe ER, but an application of ER
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="exclude_5"
                               criterionType="exclude"
                               excludeReason="not system"
                               onToggleCompleted={handleToggle}>
                        Describes a technique, method or experiment instead of a full-blown system
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="exclude_6"
                               criterionType="exclude"
                               excludeReason="secondary study"
                               onToggleCompleted={handleToggle}>
                        Is a secondary study (review, mapping study, etc.)
                    </Criterion>
                    <Criterion evidenceId={props.evidenceId} fileName={props.fileName}
                               exclusionCriteria={props.exclusionCriteria} criterionId="exclude_7"
                               criterionType="exclude"
                               excludeReason="low quality"
                               onToggleCompleted={handleToggle}>
                        Is low quality(<i>only after QA</i>)
                    </Criterion>
                </ul>
            </form>
        </aside>
    )
}