import styles from "./InclusionStatus.module.css";

type InclusionStatusProps = {
    include: boolean | "include" | "exclude";
    excludeReasons: string[];
}

export default function InclusionStatus({include, excludeReasons}: InclusionStatusProps) {
    const isIncluded = include === true || include === "include";
    if (isIncluded) {
        return (
            <div className={styles.panel}>
                <button type="submit" className={styles.btnInclude}>Include</button>
            </div>
        )
    } else {
        const reasons = Array.isArray(excludeReasons) ? excludeReasons : [];
        return (
            <div className={styles.panel}>
                <button type="submit" className={styles.btnExclude}>Exclude</button>
                <div className={styles.reasons}>
                    <span className={styles.reasonsHeading}>Reasons:</span>
                    {reasons.length > 0 ? (
                        <ul className={styles.reasonList}>
                            {reasons.map((r, idx) => (
                                <li key={idx} className={styles.reasonItem}>{r}</li>
                            ))}
                        </ul>
                    ) : (<span className={styles.noReasons}>-</span>)}
                </div>
            </div>
        )
            ;
    }
}
