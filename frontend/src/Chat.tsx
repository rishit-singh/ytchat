import { useRef, useState, useEffect } from 'react';
import { Textarea } from './components/ui/textarea';
import { Button } from '@/components/ui/button';
import YTEmbed from './components/YTEmbed';

interface Message {
    Role: string;
    Content: React.ReactNode;
}

function Message({ Role, Content }: Message) {
    return <div className={`flex flex-row gap-2 bg-gray-300 p-2 rounded-md self-${Role == "user" ? "end" :
        "start"
        }`}>
        <span className="text-sm text-gray-500">{Role}</span>
        <span className="text-sm">{Content}</span>
    </div >
}

function Chat() {
    const messagesRef = useRef<Message[]>([
        {
            Role: "assistant",
            Content: "Welcome to the chat! How can I help you today?"
        },
    ]);

    const [messages, setMessages] = useState<Message[]>(messagesRef.current);

    const [promptState, setPromptState] = useState<"idle" | "loading" | "success" | "error">("idle");

    const chatId = useRef<string | null>(null);

    const AddMessage = (message: Message) => {
        messagesRef.current = [...messagesRef.current, message];
        setMessages(messagesRef.current);
    };

    const Prompt = async (message: string) => {
        const body = chatId.current != null ? {
            input: message,
            chat_id: chatId.current
        } : { input: message };

        AddMessage({
            Role: "user",
            Content: <div className="flex flex-col gap-5">
                {message}
            </div>
        });

        AddMessage({
            Role: "assistant",
            Content: <div className="flex flex-col gap-5">
                <div>Loading...</div>
            </div>
        });

        console.log(body);
        try {
            const response = await fetch("http://localhost:8000/prompt", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(body)
            });

            if (response.ok) {
                const data = await response.json();

                console.log(data);

                if (chatId.current == null) {
                    chatId.current = data.chat_id;
                }

                messagesRef.current[messagesRef.current.length - 1] = {
                    Role: "assistant",
                    Content: <div className="flex flex-col gap-5">
                        <div>{data.response.remarks}</div>
                        {data.response.response.data.videos && data.response.response.data.videos.length > 0 && (
                            <div className="flex flex-col gap-3">
                                {data.response.response.data.videos.map((video: any) => <YTEmbed key={video.id} videoId={video.id} />)}
                            </div>
                        )}
                    </div>
                };
                setMessages([...messagesRef.current]);
                setPromptState("success");
            }
        }
        catch (e) {
            messagesRef.current[messagesRef.current.length - 1] = {
                Role: "assistant",
                Content: "Failed to generate response. Check the console for more details."
            };

            console.log(e);

            setPromptState("error");
            setMessages([...messagesRef.current]);
        }
    }

    const promptInput = useRef<HTMLTextAreaElement>(null);

    useEffect(() => {
        setMessages(messagesRef.current);
    }, []);

    return <>
        <div className="flex flex-col gap-5">
            <div className="flex flex-col gap-5 w-full h-full bg-gray-100 p-5 rounded-md overflow-y-scroll h-[600px]">
                {
                    messages.map((message, index) => <Message key={index} Role={message.Role} Content={message.Content} />)
                }
            </div>
            <div className="flex flex-row gap-3 items-center">
                <Textarea ref={promptInput} />
                <Button onClick={() => {
                    if (promptState == "loading") {
                        return;
                    }

                    Prompt(promptInput.current?.value ?? "");
                    setPromptState("loading");
                }}> {promptState == "loading" ? "Loading..." : "Send"}</Button>
            </div>
        </div>
    </>;
}

export default Chat;