function PasteBox({
    value,
    onChange,
    onSubmit,
    placeholder = "Write your paste here...",
    disabled = false,
}) 
{
    return (
        <form onSubmit={onSubmit}>
            <textarea
                value={value}
                onChange={(event) => onChange(event.target.value)}
                placeholder={placeholder}
                disabled={disabled}
                rows={12}
            />

            <button type="submit" disabled={disabled || !value.trim()}>
                {disabled ? "Saving..." : "Save paste"}
            </button>
        </form>
    );
}

export default PasteBox