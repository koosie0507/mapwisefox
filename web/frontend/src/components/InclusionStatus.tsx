type InclusionStatusProps = {
    status: "include" | "exclude" | boolean
    exclusionReasons?: string[] | string | null
}
export default function InclusionStatus({status, exclusionReasons}: InclusionStatusProps) {
    if (status === true || status === "include") {
        return <h3 style={{color: "green"}}>Included</h3>;
    } else {
        let exclusionText = "-"
        if (typeof(exclusionReasons) !== "undefined" && exclusionReasons !== null) {
            if (Array.isArray(exclusionReasons)) {
                exclusionText = exclusionReasons?.length > 0 ? exclusionReasons.join("; ") : "-"
            } else {
                exclusionText = exclusionReasons
            }
        }
        return (
            <div>
                <h3 style={{color: "red"}}>Excluded</h3>
                <span><b>Exclusion reasons:</b>{exclusionText}</span>
            </div>
        )
    }
}
