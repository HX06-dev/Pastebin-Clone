import { useState } from 'react'
import PasteBox from "./PasteBox";

function App() {
    const [content, setContent] = useState("");
    const [saving, setSaving] = useState(false);

    async function handleSubmit(event) {
    event.preventDefault();

    setSaving(true);

    try {
        const response = await fetch("http://127.0.0.1:5000/api/pastes", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ content }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to save paste");
        }

        window.location.href = `http://127.0.0.1:5000/paste/${data.id}`;
    }
    catch (error) {
        console.error(error);
        alert(error.message);
    }
    finally {
        setSaving(false);
    }
}

    return (
        <main>
            <h1>Pastebin Clone</h1>

            <PasteBox
                value={content}
                onChange={setContent}
                onSubmit={handleSubmit}
                disabled={saving}
            />
        </main>
    );
}

export default App
