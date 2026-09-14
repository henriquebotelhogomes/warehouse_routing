import React, { useState, useRef, useEffect } from "react";
import {
  Bot,
  X,
  Send,
  Sparkles,
  AlertTriangle,
} from "lucide-react";
import { useTranslation } from "../i18n/useTranslation";

interface Message {
  role: "user" | "assistant";
  content: string;
  hitl_card?: {
    token: string;
    title: string;
    description: string;
    confirm_text: string;
    cancel_text: string;
  };
}

export const CopilotDrawer: React.FC = () => {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Olá! Sou o **NexusFleet Copilot**, seu supervisor autônomo de frota. Como posso ajudar com os AMRs ou o armazém hoje?",
    },
  ]);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || input;
    if (!text.trim() || isLoading) return;

    const userMsg: Message = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setIsLoading(true);

    try {
      const res = await fetch("/api/v1/copilot/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      const data = await res.json();

      const assistantMsg: Message = {
        role: "assistant",
        content: data.reply,
        hitl_card: data.hitl_action_required ? data.hitl_card : undefined,
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: "❌ Falha ao conectar ao servidor do Copiloto.",
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmHITL = async (token: string) => {
    try {
      const res = await fetch("/api/v1/copilot/actions/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action_token: token }),
      });
      const data = await res.json();
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: `✅ **Ação Confirmada:** ${data.message}`,
        },
      ]);
    } catch (e) {
      alert("Erro ao confirmar ação.");
    }
  };

  return (
    <>
      {/* Botão Flutuante para Abrir o Copiloto */}
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-20 right-6 z-40 flex items-center gap-2.5 px-4 py-3 rounded-full bg-gradient-to-r from-cyan-500 to-blue-600 text-slate-950 font-bold shadow-2xl shadow-cyan-500/40 hover:scale-105 transition-all"
        >
          <Bot className="w-5 h-5 fill-current" />
          <span className="text-xs tracking-wide">NexusFleet AI</span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
        </button>
      )}

      {/* Drawer Lateral do Chat */}
      {isOpen && (
        <div className="fixed top-16 right-0 w-96 h-[calc(100vh-4rem)] bg-slate-900/95 backdrop-blur-xl border-l border-slate-800 shadow-2xl z-40 flex flex-col">
          {/* Header do Copiloto */}
          <div className="p-4 border-b border-slate-800 flex items-center justify-between">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-blue-600 flex items-center justify-center text-slate-950">
                <Bot className="w-5 h-5 fill-current" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white flex items-center gap-1.5">
                  {t("copilot_title")}
                  <Sparkles className="w-3 h-3 text-cyan-400" />
                </h3>
                <span className="text-[10px] text-cyan-400 font-mono">
                  {t("copilot_badge")}
                </span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Histórico de Mensagens */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex flex-col ${
                  m.role === "user" ? "items-end" : "items-start"
                }`}
              >
                <div
                  className={`max-w-[85%] p-3 rounded-2xl leading-relaxed ${
                    m.role === "user"
                      ? "bg-cyan-500 text-slate-950 font-medium rounded-br-none"
                      : "bg-slate-800/90 text-slate-200 border border-slate-700/60 rounded-bl-none shadow-sm whitespace-pre-line"
                  }`}
                >
                  {m.content}
                </div>

                {/* Cartão de Confirmação HITL */}
                {m.hitl_card && (
                  <div className="mt-2.5 p-3 rounded-xl bg-red-950/40 border border-red-500/40 w-full space-y-2">
                    <div className="flex items-center gap-1.5 text-red-400 font-bold text-xs">
                      <AlertTriangle className="w-4 h-4" />
                      {m.hitl_card.title}
                    </div>
                    <p className="text-[11px] text-slate-300">
                      {m.hitl_card.description}
                    </p>
                    <div className="flex gap-2 pt-1">
                      <button
                        onClick={() => handleConfirmHITL(m.hitl_card!.token)}
                        className="flex-1 py-1.5 bg-red-500 hover:bg-red-600 text-white font-bold rounded-lg text-[11px] transition-all shadow"
                      >
                        {m.hitl_card.confirm_text}
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))}
            {isLoading && (
              <div className="flex items-center gap-2 text-slate-500 text-[11px]">
                <Bot className="w-3.5 h-3.5 animate-spin text-cyan-400" />
                <span>Copiloto analisando malha espaço-temporal...</span>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Atalhos Rápidos para Recrutadores */}
          <div className="px-4 py-2 border-t border-slate-800 bg-slate-950/60 flex flex-col gap-1.5">
            <span className="text-[10px] text-slate-400 font-medium">
              💡 Exemplos Rápidos:
            </span>
            <div className="flex flex-wrap gap-1.5">
              <button
                onClick={() => handleSend(t("copilot_quick_prompt_1"))}
                className="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all truncate max-w-[180px]"
              >
                {t("copilot_quick_prompt_1")}
              </button>
              <button
                onClick={() => handleSend(t("copilot_quick_prompt_2"))}
                className="text-[10px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 transition-all truncate"
              >
                {t("copilot_quick_prompt_2")}
              </button>
              <button
                onClick={() => handleSend(t("copilot_quick_prompt_3"))}
                className="text-[10px] px-2 py-1 rounded bg-red-950/40 hover:bg-red-900/60 text-red-300 border border-red-800/40 transition-all truncate"
              >
                {t("copilot_quick_prompt_3")}
              </button>
            </div>
          </div>

          {/* Input de Mensagem */}
          <div className="p-3 border-t border-slate-800 bg-slate-950 flex items-center gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder={t("copilot_placeholder")}
              className="flex-1 bg-slate-900 px-3 py-2 rounded-xl text-xs text-white placeholder-slate-500 border border-slate-800 focus:outline-none focus:border-cyan-500"
            />
            <button
              onClick={() => handleSend()}
              disabled={isLoading || !input.trim()}
              className="p-2 rounded-xl bg-cyan-500 text-slate-950 hover:bg-cyan-400 disabled:opacity-40 transition-all"
            >
              <Send className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}
    </>
  );
};
