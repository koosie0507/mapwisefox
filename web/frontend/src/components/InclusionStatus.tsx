type InclusionStatusProps = {
    status: "include" | "exclude" | boolean
    exclusionReasons: Array<string>
}
export default function InclusionStatus({status, exclusionReasons}: InclusionStatusProps) {
    if (status === true || status === "include") {
        return <h3 style={{color: "green"}}>Included</h3>;
    } else {
        return (
            <div>
                <h3 style={{color: "red"}}>Excluded</h3>
                <span><b>Exclusion reasons:</b>
                {exclusionReasons?.length ? exclusionReasons.join(", ") : "—"}
                </span>
            </div>
        )
    }
}
