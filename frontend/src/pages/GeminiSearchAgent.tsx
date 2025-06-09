import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { Send, Search, Bot } from "lucide-react";

// 定义处理事件类型
export interface ProcessedEvent {
  title: string;
  data: string;
}

export default function GeminiSearchAgent() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);

  const thread = useStream<{
    messages: Message[];
    initial_search_query_count: number;
    max_research_loops: number;
    reasoning_model: string;
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : undefined,
    assistantId: "agent",
    messagesKey: "messages",
    onFinish: (event: any) => {
      console.log(event);
    },
    onUpdateEvent: (event: any) => {
      let processedEvent: ProcessedEvent | null = null;
      if (event.generate_query) {
        processedEvent = {
          title: "Generating Search Queries",
          data: event.generate_query.query_list.join(", "),
        };
      } else if (event.web_research) {
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        processedEvent = {
          title: "Web Research",
          data: `Gathered ${numSources} sources. Related to: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        processedEvent = {
          title: "Reflection",
          data: event.reflection.is_sufficient
            ? "Search successful, generating final answer."
            : `Need more information, searching for ${event.reflection.follow_up_queries.join(
                ", "
              )}`,
        };
      } else if (event.finalize_answer) {
        processedEvent = {
          title: "Finalizing Answer",
          data: "Composing and presenting the final answer.",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string, model: string) => {
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      // convert effort to, initial_search_query_count and max_research_loops
      // low means max 1 loop and 1 query
      // medium means max 3 loops and 3 queries
      // high means max 10 loops and 5 queries
      let initial_search_query_count = 0;
      let max_research_loops = 0;
      switch (effort) {
        case "low":
          initial_search_query_count = 1;
          max_research_loops = 1;
          break;
        case "medium":
          initial_search_query_count = 3;
          max_research_loops = 3;
          break;
        case "high":
          initial_search_query_count = 5;
          max_research_loops = 10;
          break;
      }

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];
      thread.submit({
        messages: newMessages,
        initial_search_query_count: initial_search_query_count,
        max_research_loops: max_research_loops,
        reasoning_model: model,
      });
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  const [inputMessage, setInputMessage] = useState("");
  const [effort, setEffort] = useState("medium");
  const [model, setModel] = useState("gemini-2.0-flash-exp");

  return (
    <div className="flex h-screen bg-gray-50">
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="bg-white border-b px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <div className="h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center mr-3">
                <Bot className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="font-semibold text-gray-900">Gemini Search Agent</h1>
                <p className="text-sm text-gray-500">AI-powered research assistant</p>
              </div>
            </div>
            {thread.isLoading && (
              <button 
                onClick={handleCancel}
                className="px-4 py-2 bg-red-500 text-white rounded-lg hover:bg-red-600"
              >
                Stop
              </button>
            )}
          </div>
        </div>

        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto p-4" ref={scrollAreaRef}>
          {thread.messages.length === 0 ? (
            /* Welcome Screen */
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="h-20 w-20 rounded-full bg-blue-500 flex items-center justify-center mb-6">
                <Bot className="h-10 w-10 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Welcome to Gemini Search Agent</h2>
              <p className="text-gray-600 mb-8 max-w-md">
                Ask me anything and I'll research it for you using advanced AI search capabilities.
              </p>
              
              {/* Settings */}
              <div className="bg-white rounded-lg p-6 shadow-sm border max-w-md w-full mb-6">
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">Research Effort</label>
                  <select 
                    value={effort} 
                    onChange={(e) => setEffort(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="low">Low (1 query, 1 loop)</option>
                    <option value="medium">Medium (3 queries, 3 loops)</option>
                    <option value="high">High (5 queries, 10 loops)</option>
                  </select>
                </div>
                
                <div className="mb-4">
                  <label className="block text-sm font-medium text-gray-700 mb-2">AI Model</label>
                  <select 
                    value={model} 
                    onChange={(e) => setModel(e.target.value)}
                    className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    <option value="gemini-2.0-flash-exp">Gemini 2.0 Flash</option>
                    <option value="gemini-1.5-pro">Gemini 1.5 Pro</option>
                    <option value="gemini-1.5-flash">Gemini 1.5 Flash</option>
                  </select>
                </div>
              </div>
            </div>
          ) : (
            /* Messages Display */
            <div className="space-y-4">
              {thread.messages.map((message, index) => (
                <div key={index} className={`flex ${message.type === "human" ? "justify-end" : "justify-start"}`}>
                  {message.type === "ai" && (
                    <div className="h-8 w-8 rounded-full bg-blue-500 mr-3 flex items-center justify-center">
                      <Bot className="h-5 w-5 text-white" />
                    </div>
                  )}
                  <div className={`max-w-[70%] rounded-2xl p-4 ${
                    message.type === "human" 
                      ? "bg-blue-500 text-white rounded-tr-none" 
                      : "bg-white shadow-sm border rounded-tl-none"
                  }`}>
                                         <div className="whitespace-pre-wrap">
                       {typeof message.content === 'string' ? message.content : 
                        Array.isArray(message.content) ? 
                          message.content.map((item: any, idx: number) => (
                            <span key={idx}>{item.text || JSON.stringify(item)}</span>
                          )) : 
                        JSON.stringify(message.content)
                       }
                     </div>
                  </div>
                </div>
              ))}
              
              {/* Activity Timeline */}
              {processedEventsTimeline.length > 0 && (
                <div className="bg-gray-100 rounded-lg p-4">
                  <h3 className="font-medium text-gray-900 mb-3">Research Progress</h3>
                  <div className="space-y-2">
                    {processedEventsTimeline.map((event, index) => (
                      <div key={index} className="flex items-start">
                        <div className="h-2 w-2 bg-blue-500 rounded-full mt-2 mr-3 flex-shrink-0"></div>
                        <div>
                          <div className="font-medium text-sm text-gray-900">{event.title}</div>
                          <div className="text-sm text-gray-600">{event.data}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {thread.isLoading && (
                <div className="flex justify-start">
                  <div className="h-8 w-8 rounded-full bg-blue-500 mr-3 flex items-center justify-center">
                    <Bot className="h-5 w-5 text-white" />
                  </div>
                  <div className="bg-white shadow-sm border rounded-2xl rounded-tl-none p-4">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-sm text-gray-500">Researching...</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Input Section */}
        <div className="bg-white border-t p-4">
          <div className="flex items-center gap-3">
            <div className="flex-1 flex items-center bg-gray-100 rounded-full">
              <textarea
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                placeholder="Ask me anything to research..."
                className="resize-none min-h-[48px] max-h-32 bg-transparent flex-1 py-3 px-4 focus:outline-none"
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    if (inputMessage.trim()) {
                      handleSubmit(inputMessage, effort, model);
                      setInputMessage("");
                    }
                  }
                }}
              />
              <div className="px-3">
                <Search className="h-5 w-5 text-gray-400" />
              </div>
            </div>
            <button 
              onClick={() => {
                if (inputMessage.trim()) {
                  handleSubmit(inputMessage, effort, model);
                  setInputMessage("");
                }
              }}
              disabled={!inputMessage.trim() || thread.isLoading}
              className="h-12 w-12 bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white rounded-full flex items-center justify-center"
            >
              <Send className="h-5 w-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
} 