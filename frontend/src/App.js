import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Card } from "./components/ui/card";
import { Button } from "./components/ui/button";
import { Select } from "./components/ui/select";
import { Textarea } from "./components/ui/textarea";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { Brain, Zap, MessageSquare, Settings, Cpu, Network, Eye, AlertTriangle, Key, Lock, Unlock } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [models, setModels] = useState({});
  const [sessions, setSessions] = useState([]);
  const [currentSession, setCurrentSession] = useState(null);
  const [hostLLM, setHostLLM] = useState({ provider: 'openai', model_name: 'gpt-4o', display_name: 'GPT-4o' });
  const [targetLLM, setTargetLLM] = useState({ provider: 'openai', model_name: 'gpt-4o-mini', display_name: 'GPT-4o Mini' });
  const [protocol, setProtocol] = useState('mcp');
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('setup');
  
  // API Keys state
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    anthropic: '',
    gemini: ''
  });
  const [showApiKeys, setShowApiKeys] = useState(false);

  const protocols = [
    { value: 'mcp', label: 'MCP Protocol', desc: 'Structured JSON communication', icon: MessageSquare },
    { value: 'gibberlink', label: 'GibberLink', desc: 'Compressed semantic encoding', icon: Zap },
    { value: 'droidspeak', label: 'DroidSpeak', desc: 'Ultra-efficient binary protocol', icon: Cpu },
    { value: 'natural', label: 'Natural Language', desc: 'Fallback natural communication', icon: Brain }
  ];

  useEffect(() => {
    fetchModels();
    fetchSessions();
  }, []);

  const fetchModels = async () => {
    try {
      const response = await axios.get(`${API}/models`);
      setModels(response.data);
    } catch (error) {
      console.error('Failed to fetch models:', error);
      setError('Failed to load models');
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await axios.get(`${API}/sessions`);
      setSessions(response.data);
    } catch (error) {
      console.error('Failed to fetch sessions:', error);
    }
  };

  const createSession = async () => {
    try {
      setError(null);
      
      // Check if required API keys are provided
      const hostKey = apiKeys[hostLLM.provider];
      const targetKey = apiKeys[targetLLM.provider];
      
      if (!hostKey && hostLLM.provider !== 'openai') {
        setError(`Please provide ${hostLLM.provider.charAt(0).toUpperCase() + hostLLM.provider.slice(1)} API key for the host LLM`);
        return;
      }
      
      if (!targetKey && targetLLM.provider !== 'openai') {
        setError(`Please provide ${targetLLM.provider.charAt(0).toUpperCase() + targetLLM.provider.slice(1)} API key for the target LLM`);
        return;
      }
      
      const sessionData = {
        host_llm: hostLLM,
        target_llm: targetLLM,
        protocol: protocol,
        api_keys: {
          openai: apiKeys.openai,
          anthropic: apiKeys.anthropic,
          gemini: apiKeys.gemini
        }
      };
      
      const response = await axios.post(`${API}/session`, sessionData);
      setCurrentSession(response.data);
      setSessions([...sessions, response.data]);
      setActiveTab('communicate');
    } catch (error) {
      console.error('Failed to create session:', error);
      setError(error.response?.data?.detail || 'Failed to create session');
    }
  };

  const extractInformation = async () => {
    if (!currentSession || !query.trim()) return;
    
    setIsExtracting(true);
    setError(null);
    setResult(null);
    
    try {
      const response = await axios.post(`${API}/extract`, {
        session_id: currentSession.id,
        query: query.trim(),
        protocol: protocol
      });
      
      setResult(response.data);
      setActiveTab('results');
    } catch (error) {
      console.error('Extraction failed:', error);
      
      // Handle different error types
      if (error.response?.status === 429) {
        setError('API quota exceeded. Please check your OpenAI billing plan or try again later.');
      } else if (error.response?.status === 401) {
        setError('API authentication failed. Please check your API keys.');
      } else if (error.response?.status === 400 && error.response?.data?.detail?.includes('only OpenAI')) {
        setError(error.response.data.detail);
      } else {
        setError(error.response?.data?.detail || 'Extraction failed. Please try again.');
      }
      
    } finally {
      setIsExtracting(false);
    }
  };

  const ModelSelector = ({ title, selectedModel, onModelChange, models }) => (
    <Card className="p-6 backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <Brain className="w-5 h-5 text-blue-400" />
        {title}
      </h3>
      
      <div className="space-y-4">
        <div>
          <label className="text-sm text-slate-300 mb-2 block">Provider</label>
          <select 
            className="w-full p-3 bg-slate-800 border border-slate-600 rounded-lg text-white focus:border-blue-400 focus:outline-none"
            value={selectedModel.provider}
            onChange={(e) => {
              const provider = e.target.value;
              const firstModel = models[provider]?.[0];
              if (firstModel) {
                onModelChange({
                  provider,
                  model_name: firstModel.model_name,
                  display_name: firstModel.display_name
                });
              }
            }}
          >
            {Object.keys(models).map(provider => (
              <option key={provider} value={provider}>
                {provider.charAt(0).toUpperCase() + provider.slice(1)}
              </option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="text-sm text-slate-300 mb-2 block">Model</label>
          <select
            className="w-full p-3 bg-slate-800 border border-slate-600 rounded-lg text-white focus:border-blue-400 focus:outline-none"
            value={selectedModel.model_name}
            onChange={(e) => {
              const modelName = e.target.value;
              const model = models[selectedModel.provider]?.find(m => m.model_name === modelName);
              if (model) {
                onModelChange({
                  ...selectedModel,
                  model_name: model.model_name,
                  display_name: model.display_name
                });
              }
            }}
          >
            {models[selectedModel.provider]?.map(model => (
              <option key={model.model_name} value={model.model_name}>
                {model.display_name}
              </option>
            ))}
          </select>
        </div>
        
        <Badge className="bg-blue-900 text-blue-200 border-blue-700">
          {selectedModel.display_name}
        </Badge>
      </div>
    </Card>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-6 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-400 via-purple-400 to-cyan-400 bg-clip-text text-transparent mb-4">
            Neural Bridge
          </h1>
          <p className="text-xl text-slate-400 max-w-3xl mx-auto">
            Advanced LLM-to-LLM Communication Hub with Multi-Protocol Information Extraction
          </p>
          <div className="flex items-center justify-center gap-4 mt-6">
            <div className="flex items-center gap-2 text-green-400">
              <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
              <span className="text-sm">System Online</span>
            </div>
            <div className="flex items-center gap-2 text-blue-400">
              <Network className="w-4 h-4" />
              <span className="text-sm">{sessions.length} Active Sessions</span>
            </div>
          </div>
        </div>

        {/* Main Interface */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-4 mb-8 bg-slate-800 border border-slate-700">
            <TabsTrigger value="setup" className="data-[state=active]:bg-blue-600">
              <Settings className="w-4 h-4 mr-2" />
              Setup
            </TabsTrigger>
            <TabsTrigger value="communicate" className="data-[state=active]:bg-blue-600">
              <MessageSquare className="w-4 h-4 mr-2" />
              Communicate
            </TabsTrigger>
            <TabsTrigger value="results" className="data-[state=active]:bg-blue-600">
              <Eye className="w-4 h-4 mr-2" />
              Results
            </TabsTrigger>
            <TabsTrigger value="monitor" className="data-[state=active]:bg-blue-600">
              <Network className="w-4 h-4 mr-2" />
              Monitor
            </TabsTrigger>
          </TabsList>

          {/* Setup Tab */}
          <TabsContent value="setup" className="space-y-8">
            {/* API Keys Configuration */}
            <Card className="p-6 backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <Key className="w-5 h-5 text-yellow-400" />
                  API Keys Configuration
                </h3>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowApiKeys(!showApiKeys)}
                  className="border-slate-600 text-slate-300 hover:text-white"
                >
                  {showApiKeys ? (
                    <>
                      <Lock className="w-4 h-4 mr-2" />
                      Hide Keys
                    </>
                  ) : (
                    <>
                      <Unlock className="w-4 h-4 mr-2" />
                      Show Keys
                    </>
                  )}
                </Button>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
                <div>
                  <label className="text-sm text-slate-300 mb-2 block font-medium">
                    OpenAI API Key
                  </label>
                  <input
                    type={showApiKeys ? "text" : "password"}
                    placeholder="sk-proj-..."
                    value={apiKeys.openai}
                    onChange={(e) => setApiKeys({...apiKeys, openai: e.target.value})}
                    className="w-full p-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-blue-400 focus:outline-none"
                  />
                </div>
                
                <div>
                  <label className="text-sm text-slate-300 mb-2 block font-medium">
                    Anthropic API Key
                  </label>
                  <input
                    type={showApiKeys ? "text" : "password"}
                    placeholder="sk-ant-..."
                    value={apiKeys.anthropic}
                    onChange={(e) => setApiKeys({...apiKeys, anthropic: e.target.value})}
                    className="w-full p-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-blue-400 focus:outline-none"
                  />
                </div>
                
                <div>
                  <label className="text-sm text-slate-300 mb-2 block font-medium">
                    Gemini API Key
                  </label>
                  <input
                    type={showApiKeys ? "text" : "password"}
                    placeholder="AI..."
                    value={apiKeys.gemini}
                    onChange={(e) => setApiKeys({...apiKeys, gemini: e.target.value})}
                    className="w-full p-3 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:border-blue-400 focus:outline-none"
                  />
                </div>
              </div>
              
              <div className="bg-blue-900/30 border border-blue-700 rounded-lg p-4">
                <div className="flex items-start gap-3">
                  <Key className="w-5 h-5 text-blue-400 mt-0.5" />
                  <div>
                    <h4 className="text-blue-200 font-semibold mb-2">How to get API Keys:</h4>
                    <ul className="text-blue-300 text-sm space-y-1">
                      <li><strong>OpenAI:</strong> Visit <a href="https://platform.openai.com/api-keys" target="_blank" className="underline hover:text-blue-200">platform.openai.com/api-keys</a></li>
                      <li><strong>Anthropic:</strong> Visit <a href="https://console.anthropic.com/" target="_blank" className="underline hover:text-blue-200">console.anthropic.com</a></li>
                      <li><strong>Gemini:</strong> Visit <a href="https://makersuite.google.com/app/apikey" target="_blank" className="underline hover:text-blue-200">makersuite.google.com/app/apikey</a></li>
                    </ul>
                    <p className="text-blue-300 text-sm mt-2">
                      <strong>Note:</strong> Your API keys are only stored in your browser session and sent securely to the server for LLM communication.
                    </p>
                  </div>
                </div>
              </div>
            </Card>

            {/* Error Display */}
            {error && (
              <Card className="p-4 backdrop-blur-sm bg-gradient-to-br from-red-900/80 to-red-800/80 border-red-700">
                <div className="flex items-center gap-3">
                  <AlertTriangle className="w-5 h-5 text-red-400" />
                  <div>
                    <h4 className="text-red-200 font-semibold">Configuration Error</h4>
                    <p className="text-red-300 text-sm">{error}</p>
                  </div>
                </div>
              </Card>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
              <ModelSelector
                title="Host LLM (Information Extractor)"
                selectedModel={hostLLM}
                onModelChange={setHostLLM}
                models={models}
              />
              <ModelSelector
                title="Target LLM (Information Source)"
                selectedModel={targetLLM}
                onModelChange={setTargetLLM}
                models={models}
              />
            </div>

            {/* Protocol Selection */}
            <Card className="p-6 backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-6">Communication Protocol</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {protocols.map((p) => {
                  const IconComponent = p.icon;
                  return (
                    <div
                      key={p.value}
                      onClick={() => setProtocol(p.value)}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all duration-200 hover:scale-105 ${
                        protocol === p.value
                          ? 'border-blue-500 bg-blue-900/30'
                          : 'border-slate-600 bg-slate-800/50 hover:border-slate-500'
                      }`}
                    >
                      <IconComponent className={`w-6 h-6 mb-3 ${protocol === p.value ? 'text-blue-400' : 'text-slate-400'}`} />
                      <h4 className={`font-semibold mb-2 ${protocol === p.value ? 'text-blue-300' : 'text-white'}`}>
                        {p.label}
                      </h4>
                      <p className="text-sm text-slate-400">{p.desc}</p>
                    </div>
                  );
                })}
              </div>
            </Card>

            <div className="text-center">
              <Button 
                onClick={createSession}
                className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 px-8 py-3 text-lg"
                disabled={!Object.keys(models).length}
              >
                <Zap className="w-5 h-5 mr-2" />
                Initialize Communication Bridge
              </Button>
              
              <div className="mt-4 text-center">
                <p className="text-slate-400 text-sm">
                  {!apiKeys.openai && !apiKeys.anthropic && !apiKeys.gemini 
                    ? "💡 Demo mode available - try queries with 'demo' or 'test'" 
                    : "✅ Custom API keys configured - full LLM communication enabled"
                  }
                </p>
              </div>
            </div>
          </TabsContent>

          {/* Communication Tab */}
          <TabsContent value="communicate" className="space-y-6">
            {currentSession ? (
              <div className="space-y-6">
                {/* Error Display */}
                {error && (
                  <Card className="p-4 backdrop-blur-sm bg-gradient-to-br from-red-900/80 to-red-800/80 border-red-700">
                    <div className="flex items-center gap-3">
                      <AlertTriangle className="w-5 h-5 text-red-400" />
                      <div>
                        <h4 className="text-red-200 font-semibold">Error</h4>
                        <p className="text-red-300 text-sm">{error}</p>
                      </div>
                    </div>
                  </Card>
                )}
                
                <Card className="p-6 backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Active Communication Session</h3>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-slate-400">Host:</span>
                      <p className="text-white">{currentSession.host_llm.display_name}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Target:</span>
                      <p className="text-white">{currentSession.target_llm.display_name}</p>
                    </div>
                    <div>
                      <span className="text-slate-400">Protocol:</span>
                      <Badge className="ml-2 bg-blue-900 text-blue-200">{currentSession.protocol.toUpperCase()}</Badge>
                    </div>
                  </div>
                </Card>

                <Card className="p-6 backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Information Extraction Query</h3>
                  <Textarea
                    placeholder='Try "demo" or "test" for a demonstration, or enter your own query (e.g., "What are your core capabilities and limitations?")'
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="min-h-32 bg-slate-800 border-slate-600 text-white resize-none focus:border-blue-400"
                  />
                  
                  {/* Demo and OpenAI Info */}
                  <div className="mt-4 space-y-3">
                    <div className="p-3 bg-green-900/30 border border-green-700 rounded-lg">
                      <div className="flex items-center gap-2">
                        <Zap className="w-4 h-4 text-green-400" />
                        <p className="text-green-200 text-sm">
                          <strong>Demo Mode:</strong> Type "demo" or "test" in your query to see a fully functional demonstration of LLM-to-LLM communication!
                        </p>
                      </div>
                    </div>
                    
                    <div className="p-3 bg-amber-900/30 border border-amber-700 rounded-lg">
                      <div className="flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-amber-400" />
                        <p className="text-amber-200 text-sm">
                          <strong>Live API:</strong> For real LLM communication, ensure both Host and Target are set to OpenAI models and you have sufficient API quota.
                        </p>
                      </div>
                    </div>
                  </div>
                  
                  <Button 
                    onClick={extractInformation}
                    disabled={!query.trim() || isExtracting}
                    className="mt-4 bg-gradient-to-r from-green-600 to-blue-600 hover:from-green-700 hover:to-blue-700"
                  >
                    {isExtracting ? (
                      <>
                        <div className="w-4 h-4 mr-2 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        Extracting...
                      </>
                    ) : (
                      <>
                        <Brain className="w-4 h-4 mr-2" />
                        Extract Information
                      </>
                    )}
                  </Button>
                </Card>
              </div>
            ) : (
              <Card className="p-12 text-center backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
                <Brain className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-slate-400 mb-2">No Active Session</h3>
                <p className="text-slate-500 mb-6">Create a communication session in the Setup tab to begin</p>
                <Button onClick={() => setActiveTab('setup')} className="bg-blue-600 hover:bg-blue-700">
                  Go to Setup
                </Button>
              </Card>
            )}
          </TabsContent>

          {/* Results Tab */}
          <TabsContent value="results" className="space-y-6">
            {error ? (
              <Card className="p-6 backdrop-blur-sm bg-gradient-to-br from-red-900/80 to-red-800/80 border-red-700">
                <h3 className="text-lg font-semibold text-red-200 mb-4 flex items-center gap-2">
                  <AlertTriangle className="w-5 h-5" />
                  Extraction Failed
                </h3>
                <p className="text-red-300">{error}</p>
                <Button 
                  onClick={() => setError(null)}
                  className="mt-4 bg-red-700 hover:bg-red-600"
                >
                  Clear Error
                </Button>
              </Card>
            ) : result ? (
              <div className="space-y-6">
                <Card className="p-6 backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
                  <h3 className="text-lg font-semibold text-white mb-4">Extraction Results</h3>
                  <div className="space-y-4">
                    <div>
                      <h4 className="text-sm font-medium text-slate-300 mb-2">Query:</h4>
                      <p className="text-white bg-slate-800 p-3 rounded border border-slate-600">{result.query}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-300 mb-2">Target Response:</h4>
                      <p className="text-white bg-slate-800 p-3 rounded border border-slate-600 whitespace-pre-wrap">{result.target_response}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-300 mb-2">Host Analysis:</h4>
                      <p className="text-white bg-slate-800 p-3 rounded border border-slate-600 whitespace-pre-wrap">{result.host_analysis}</p>
                    </div>
                    <div>
                      <h4 className="text-sm font-medium text-slate-300 mb-2">Protocol Used:</h4>
                      <Badge className="bg-blue-900 text-blue-200">{result.protocol_used?.toUpperCase()}</Badge>
                    </div>
                  </div>
                </Card>
              </div>
            ) : (
              <Card className="p-12 text-center backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
                <Eye className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <h3 className="text-xl font-semibold text-slate-400 mb-2">No Results Yet</h3>
                <p className="text-slate-500">Run an information extraction to see results here</p>
              </Card>
            )}
          </TabsContent>

          {/* Monitor Tab */}
          <TabsContent value="monitor" className="space-y-6">
            <Card className="p-6 backdrop-blur-sm bg-gradient-to-br from-slate-900/80 to-slate-800/80 border-slate-700">
              <h3 className="text-lg font-semibold text-white mb-4">Session History</h3>
              {sessions.length > 0 ? (
                <div className="space-y-3">
                  {sessions.map((session) => (
                    <div key={session.id} className="p-4 bg-slate-800 rounded border border-slate-600">
                      <div className="flex justify-between items-start">
                        <div>
                          <p className="text-white font-medium">
                            {session.host_llm.display_name} ↔ {session.target_llm.display_name}
                          </p>
                          <p className="text-slate-400 text-sm">
                            Protocol: {session.protocol.toUpperCase()} | Created: {new Date(session.created_at).toLocaleString()}
                          </p>
                        </div>
                        <Badge 
                          className={`${
                            session.status === 'active' 
                              ? 'bg-green-900 text-green-200' 
                              : 'bg-slate-900 text-slate-200'
                          }`}
                        >
                          {session.status}
                        </Badge>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-slate-500 text-center py-8">No sessions created yet</p>
              )}
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}

export default App;