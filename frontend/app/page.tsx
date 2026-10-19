"use client";

import { useRef, useState } from "react";

type Mode = "SALE" | "ASK";

export default function Home() {
  const [mode, setMode] = useState<Mode>("SALE");

  const [isRecording, setIsRecording] = useState(false);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);

  const [isTranscribing, setIsTranscribing] = useState(false);
  const [transcript, setTranscript] = useState("");

  const [isPreparing, setIsPreparing] = useState(false);
  const [confirmationId, setConfirmationId] = useState<number | null>(null);
  const [confirmationSummary, setConfirmationSummary] = useState("");
  const [clarificationQuestions, setClarificationQuestions] = useState<
    string[]
  >([]);

  const [clarificationAnswer, setClarificationAnswer] = useState("");
  const [isClarifying, setIsClarifying] = useState(false);

  const [isConfirming, setIsConfirming] = useState(false);
  const [resultMessage, setResultMessage] = useState("");
  const [saleId, setSaleId] = useState<number | null>(null);

  const [isAnswering, setIsAnswering] = useState(false);
  const [assistantAnswer, setAssistantAnswer] = useState("");
  const [detectedIntent, setDetectedIntent] = useState("");

  const [error, setError] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  function resetInteractionState() {
    setTranscript("");
    setConfirmationId(null);
    setConfirmationSummary("");
    setClarificationQuestions([]);
    setClarificationAnswer("");
    setResultMessage("");
    setSaleId(null);
    setAssistantAnswer("");
    setDetectedIntent("");
    setError(null);
  }

  function changeMode(nextMode: Mode) {
    resetInteractionState();

    setAudioBlob(null);

    if (audioUrl) {
      URL.revokeObjectURL(audioUrl);
      setAudioUrl(null);
    }

    setMode(nextMode);
  }

  async function startRecording() {
    try {
      resetInteractionState();

      setAudioBlob(null);

      if (audioUrl) {
        URL.revokeObjectURL(audioUrl);
        setAudioUrl(null);
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        audio: true,
      });

      const recorder = new MediaRecorder(stream);

      chunksRef.current = [];

      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      recorder.onstop = () => {
        const blob = new Blob(chunksRef.current, {
          type: recorder.mimeType || "audio/webm",
        });

        const url = URL.createObjectURL(blob);

        setAudioBlob(blob);
        setAudioUrl(url);

        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current = recorder;

      recorder.start();
      setIsRecording(true);
    } catch (err) {
      console.error(err);

      setError(
        "Microphone access failed. Please allow microphone permission and try again.",
      );
    }
  }

  function stopRecording() {
    const recorder = mediaRecorderRef.current;

    if (!recorder) {
      return;
    }

    if (recorder.state !== "inactive") {
      recorder.stop();
    }

    setIsRecording(false);
  }

  async function toggleRecording() {
    if (isRecording) {
      stopRecording();
    } else {
      await startRecording();
    }
  }

  async function transcribeRecording() {
    if (!audioBlob) {
      return;
    }

    try {
      setError(null);
      setIsTranscribing(true);
      setTranscript("");
      setAssistantAnswer("");
      setDetectedIntent("");
      setConfirmationId(null);
      setConfirmationSummary("");
      setClarificationQuestions([]);
      setClarificationAnswer("");
      setResultMessage("");
      setSaleId(null);

      const formData = new FormData();

      formData.append(
        "file",
        audioBlob,
        "recording.webm",
      );

      const response = await fetch(
        "http://127.0.0.1:8000/voice/transcribe",
        {
          method: "POST",
          body: formData,
        },
      );

      if (!response.ok) {
        throw new Error(
          `Transcription failed with status ${response.status}`,
        );
      }

      const data = await response.json();

      setTranscript(data.transcript);
    } catch (err) {
      console.error(err);

      setError(
        "Transcription failed. Make sure the backend is running and try again.",
      );
    } finally {
      setIsTranscribing(false);
    }
  }

  async function prepareSale() {
    if (!transcript) {
      return;
    }

    try {
      setError(null);
      setIsPreparing(true);
      setConfirmationId(null);
      setConfirmationSummary("");
      setClarificationQuestions([]);
      setClarificationAnswer("");
      setResultMessage("");
      setSaleId(null);

      const response = await fetch(
        "http://127.0.0.1:8000/voice/prepare?business_id=1",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: transcript,
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : "Could not prepare the sale.";

        throw new Error(detail);
      }

      setConfirmationId(data.confirmation_id);
      setConfirmationSummary(data.confirmation_summary);
      setClarificationQuestions(
        data.clarification_questions ?? [],
      );
    } catch (err) {
      console.error(err);

      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Could not prepare the sale.");
      }
    } finally {
      setIsPreparing(false);
    }
  }

  async function submitClarification() {
    if (!confirmationId || !clarificationAnswer.trim()) {
      return;
    }

    try {
      setError(null);
      setIsClarifying(true);

      const response = await fetch(
        "http://127.0.0.1:8000/voice/clarify",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            confirmation_id: confirmationId,
            answer: clarificationAnswer.trim(),
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : "Could not apply clarification.";

        throw new Error(detail);
      }

      setConfirmationSummary(data.confirmation_summary);
      setClarificationQuestions(
        data.clarification_questions ?? [],
      );

      setClarificationAnswer("");
    } catch (err) {
      console.error(err);

      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Could not apply clarification.");
      }
    } finally {
      setIsClarifying(false);
    }
  }

  async function confirmSale(confirmed: boolean) {
    if (!confirmationId) {
      return;
    }

    try {
      setError(null);
      setIsConfirming(true);
      setResultMessage("");
      setSaleId(null);

      const response = await fetch(
        "http://127.0.0.1:8000/voice/confirm",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            confirmation_id: confirmationId,
            confirmed,
          }),
        },
      );

      const data = await response.json();

      if (!response.ok) {
        const detail =
          typeof data.detail === "string"
            ? data.detail
            : "Could not complete the sale.";

        throw new Error(detail);
      }

      if (confirmed) {
        setResultMessage(
          `Sale created successfully. Sale ID: ${data.sale_id}`,
        );

        setSaleId(data.sale_id);
      } else {
        setResultMessage("Sale cancelled.");
      }

      setConfirmationSummary("");
      setConfirmationId(null);
      setClarificationQuestions([]);
      setClarificationAnswer("");
    } catch (err) {
      console.error(err);

      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Could not complete the sale.");
      }
    } finally {
      setIsConfirming(false);
    }
  }

  async function askAssistant() {
    if (!transcript) {
      return;
    }

    try {
      setError(null);
      setIsAnswering(true);
      setAssistantAnswer("");
      setDetectedIntent("");

      const intentResponse = await fetch(
        "http://127.0.0.1:8000/assistant/intent",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            text: transcript,
          }),
        },
      );

      const intentData = await intentResponse.json();

      if (!intentResponse.ok) {
        throw new Error(
          "Could not determine what you are asking.",
        );
      }

      setDetectedIntent(intentData.intent);

      if (intentData.intent === "CHECK_INVENTORY") {
        const inventoryResponse = await fetch(
          "http://127.0.0.1:8000/assistant/inventory?business_id=1",
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              text: transcript,
            }),
          },
        );

        const inventoryData = await inventoryResponse.json();

        if (!inventoryResponse.ok) {
          throw new Error(
            "Could not check inventory.",
          );
        }

        setAssistantAnswer(inventoryData.answer);
        return;
      }

      setAssistantAnswer(
        `I understood this as ${intentData.intent}, but that type of question is not connected yet.`,
      );
    } catch (err) {
      console.error(err);

      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError(
          "Could not answer the question.",
        );
      }
    } finally {
      setIsAnswering(false);
    }
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto flex min-h-screen max-w-md flex-col px-6 py-8">
        <header className="mb-6">
          <p className="text-sm font-medium text-slate-400">
            Voice Inventory
          </p>

          <h1 className="mt-2 text-3xl font-bold tracking-tight">
            {mode === "SALE"
              ? "Record a sale"
              : "Ask your business"}
          </h1>

          <p className="mt-3 text-sm leading-6 text-slate-400">
            {mode === "SALE"
              ? "Describe the customer, products, quantity, amount, and payment method."
              : "Ask a question about inventory or your business data."}
          </p>
        </header>

        <div className="mb-8 grid grid-cols-2 rounded-2xl bg-slate-900 p-1">
          <button
            type="button"
            onClick={() => changeMode("SALE")}
            className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${
              mode === "SALE"
                ? "bg-white text-slate-950"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Record sale
          </button>

          <button
            type="button"
            onClick={() => changeMode("ASK")}
            className={`rounded-xl px-4 py-3 text-sm font-semibold transition ${
              mode === "ASK"
                ? "bg-white text-slate-950"
                : "text-slate-400 hover:text-white"
            }`}
          >
            Ask
          </button>
        </div>

        <section className="flex flex-1 flex-col items-center justify-center">
          <button
            type="button"
            onClick={toggleRecording}
            disabled={
              isConfirming ||
              isClarifying ||
              isAnswering
            }
            className={`flex h-40 w-40 items-center justify-center rounded-full text-lg font-semibold shadow-lg transition ${
              isRecording
                ? "bg-red-500 hover:bg-red-400"
                : "bg-white text-slate-950 hover:bg-slate-200"
            } disabled:cursor-not-allowed disabled:opacity-50`}
          >
            {isRecording ? "Stop" : "Record"}
          </button>

          <p className="mt-6 text-sm text-slate-400">
            {isRecording
              ? "Recording... tap again to stop."
              : "Ready to record."}
          </p>

          {error && (
            <div className="mt-5 w-full rounded-2xl border border-red-900 bg-red-950/30 p-4">
              <p className="text-sm text-red-300">
                {error}
              </p>
            </div>
          )}

          {audioUrl && !isRecording && (
            <div className="mt-8 w-full rounded-2xl border border-slate-800 bg-slate-900 p-4">
              <p className="mb-3 text-sm font-medium text-slate-300">
                Recorded audio
              </p>

              <audio
                controls
                src={audioUrl}
                className="w-full"
              />

              <button
                type="button"
                onClick={transcribeRecording}
                disabled={isTranscribing}
                className="mt-4 w-full rounded-xl bg-white px-4 py-3 font-semibold text-slate-950 transition hover:bg-slate-200 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {isTranscribing
                  ? "Transcribing..."
                  : "Transcribe recording"}
              </button>
            </div>
          )}

          {transcript && (
            <div className="mt-6 w-full rounded-2xl border border-emerald-900 bg-emerald-950/30 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                Transcript
              </p>

              <p className="mt-3 text-sm leading-6 text-slate-200">
                {transcript}
              </p>

              {mode === "SALE" ? (
                <button
                  type="button"
                  onClick={prepareSale}
                  disabled={isPreparing}
                  className="mt-4 w-full rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isPreparing
                    ? "Preparing sale..."
                    : "Review sale"}
                </button>
              ) : (
                <button
                  type="button"
                  onClick={askAssistant}
                  disabled={isAnswering}
                  className="mt-4 w-full rounded-xl bg-cyan-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-cyan-300 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  {isAnswering
                    ? "Checking..."
                    : "Ask"}
                </button>
              )}
            </div>
          )}

          {mode === "ASK" && assistantAnswer && (
            <div className="mt-6 w-full rounded-2xl border border-cyan-900 bg-cyan-950/30 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-cyan-400">
                Answer
              </p>

              <p className="mt-3 text-lg font-semibold leading-7 text-white">
                {assistantAnswer}
              </p>

              {detectedIntent && (
                <p className="mt-4 text-xs text-slate-500">
                  Intent: {detectedIntent}
                </p>
              )}
            </div>
          )}

          {mode === "SALE" && confirmationSummary && (
            <div className="mt-6 w-full rounded-2xl border border-slate-700 bg-slate-900 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
                Sale review
              </p>

              <p className="mt-3 text-sm leading-6 text-slate-200">
                {confirmationSummary}
              </p>

              {clarificationQuestions.length > 0 && (
                <div className="mt-4 rounded-xl border border-amber-900 bg-amber-950/30 p-4">
                  <p className="text-sm font-medium text-amber-400">
                    More information needed
                  </p>

                  <ul className="mt-3 space-y-2 text-sm text-slate-300">
                    {clarificationQuestions.map((question) => (
                      <li key={question}>
                        {question}
                      </li>
                    ))}
                  </ul>

                  <label
                    htmlFor="clarification"
                    className="mt-5 block text-xs font-semibold uppercase tracking-wider text-slate-500"
                  >
                    Your answer
                  </label>

                  <textarea
                    id="clarification"
                    value={clarificationAnswer}
                    onChange={(event) =>
                      setClarificationAnswer(
                        event.target.value,
                      )
                    }
                    placeholder="Example: I mean the Ceramic Cup Set."
                    rows={3}
                    className="mt-2 w-full resize-none rounded-xl border border-slate-700 bg-slate-950 px-4 py-3 text-sm text-white outline-none transition placeholder:text-slate-600 focus:border-amber-500"
                  />

                  <button
                    type="button"
                    onClick={submitClarification}
                    disabled={
                      isClarifying ||
                      !clarificationAnswer.trim()
                    }
                    className="mt-3 w-full rounded-xl bg-amber-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-amber-300 disabled:cursor-not-allowed disabled:opacity-50"
                  >
                    {isClarifying
                      ? "Applying clarification..."
                      : "Submit clarification"}
                  </button>
                </div>
              )}

              {confirmationId &&
                clarificationQuestions.length === 0 && (
                  <>
                    <p className="mt-4 text-xs text-slate-500">
                      Confirmation ID: {confirmationId}
                    </p>

                    <div className="mt-5 grid grid-cols-2 gap-3">
                      <button
                        type="button"
                        onClick={() => confirmSale(false)}
                        disabled={isConfirming}
                        className="rounded-xl border border-slate-700 px-4 py-3 font-semibold text-slate-200 transition hover:bg-slate-800 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        Cancel
                      </button>

                      <button
                        type="button"
                        onClick={() => confirmSale(true)}
                        disabled={isConfirming}
                        className="rounded-xl bg-emerald-400 px-4 py-3 font-semibold text-slate-950 transition hover:bg-emerald-300 disabled:cursor-not-allowed disabled:opacity-50"
                      >
                        {isConfirming
                          ? "Saving..."
                          : "Confirm sale"}
                      </button>
                    </div>
                  </>
                )}
            </div>
          )}

          {mode === "SALE" && resultMessage && (
            <div className="mt-6 w-full rounded-2xl border border-emerald-800 bg-emerald-950/40 p-5">
              <p className="text-xs font-semibold uppercase tracking-wider text-emerald-400">
                Done
              </p>

              <p className="mt-3 text-sm leading-6 text-slate-200">
                {resultMessage}
              </p>

              {saleId && (
                <p className="mt-2 text-xs text-slate-500">
                  Sale ID: {saleId}
                </p>
              )}
            </div>
          )}
        </section>

        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-5">
          <p className="text-xs font-semibold uppercase tracking-wider text-slate-500">
            {mode === "SALE"
              ? "Sale example"
              : "Question example"}
          </p>

          <p className="mt-3 text-sm leading-6 text-slate-300">
            {mode === "SALE"
              ? "“ABC bought two ceramic cup sets for sixty dollars and paid by card.”"
              : "“How many ceramic cup sets do I have left?”"}
          </p>
        </section>
      </div>
    </main>
  );
}