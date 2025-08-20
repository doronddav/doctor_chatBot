import { useEffect, useRef, useState } from "react";
import classes from "./ChatBot.module.scss";

const ChatBot = () => {
    const [messages, setMessages] = useState([
        { sender: "bot", text: "שלום!" },
    ]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const userName = "משתמש";
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };
    useEffect(() => {
        scrollToBottom();
    }, [messages]);
    const handleSend = async () => {
        if (!input.trim()) return;
        console.log(555);
        const userMessage = { sender: "user", text: input };
        setMessages((prev) => [...prev, userMessage]);
        const currentInput = input;
        setInput("");
        setLoading(true);

        try {
            const res = await fetch("http://127.0.0.1:5000/api/chatBot/chat", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    message: currentInput,
                    name: userName,
                    action: "chat",
                }),
            });

            const data = await res.json();
            if (data.reply) {
                setMessages((prev) => [
                    ...prev,
                    { sender: "bot", text: data.reply },
                ]);
            } else {
                setMessages((prev) => [
                    ...prev,
                    { sender: "bot", text: "שגיאה בהבנת הבקשה." },
                ]);
            }
        } catch (err) {
            console.error("Error:", err);
            setMessages((prev) => [
                ...prev,
                { sender: "bot", text: "התרחשה שגיאה. נסה שוב מאוחר יותר." },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyPress = (e) => {
        if (e.key === "Enter") handleSend();
    };

    return (
        <div className={classes.chatContainer}>
            <div className={classes.messages}>
                {messages.map((msg, idx) => (
                    <div
                        key={idx}
                        className={
                            msg.sender === "user"
                                ? classes.userMessage
                                : classes.botMessage
                        }
                        ref={messagesEndRef}
                    >
                        {msg.text}
                    </div>
                ))}
                {loading && <div className={classes.botMessage}>...</div>}
            </div>
            <div className={classes.inputArea}>
                <input
                    type="text"
                    placeholder="כתוב הודעה..."
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyPress={handleKeyPress}
                />
                <button onClick={handleSend} disabled={loading}>
                    שלח
                </button>
            </div>
        </div>
    );
};

export default ChatBot;
