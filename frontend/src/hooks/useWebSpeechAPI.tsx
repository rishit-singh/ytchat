import { useState } from "react";

export function useWebSpeechAPI({
    onResult
}: {
    onResult: (result: string) => void;
}) {
    const [listening, setListening] = useState<boolean>(false);

    const SpeechRecognition = new (window?.SpeechRecognition || window?.webkitSpeechRecognition)();

    SpeechRecognition.continuous = true;
    SpeechRecognition.lang = 'en-US';
    SpeechRecognition.interimResults = false;
    // SpeechRecognition.maxAlternatives = 1;

    SpeechRecognition.onresult = (event: SpeechRecognitionEvent) => {
        const result = event.results[event.results.length - 1][0].transcript;
        onResult(result);
    };
    
    SpeechRecognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('Speech recognition error', event);
        setListening(false);
    };

    return {
        listening, 
        start: () => { SpeechRecognition.start(); setListening(true); },
        stop: () => { setListening(false); SpeechRecognition.stop(); },
    };
}