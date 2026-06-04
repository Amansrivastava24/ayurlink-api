import { useState, useEffect, useCallback } from 'react'
import { 
  Search, 
  ArrowRight, 
  Database, 
  Shuffle, 
  Terminal, 
  HelpCircle, 
  AlertCircle, 
  BookOpen, 
  Code,
  Layers,
  Copy,
  Check
} from 'lucide-react'

// Constants matching backend systems and endpoints
const BACKEND_URL = 'http://127.0.0.1:8000'

interface Term {
  code: string
  display: string
  system: string
  translation?: string
  definition?: string
  icd11_mms_code?: string
  icd11_mms_display?: string
  icd11_tm2_code?: string
  icd11_tm2_display?: string
}

export default function App() {
  // Navigation
  const [activeTab, setActiveTab] = useState<'search' | 'translate' | 'explore'>('search')
  const [backendConnected, setBackendConnected] = useState<boolean>(true)
  
  // Search state
  const [searchQuery, setSearchQuery] = useState('')
  const [searchSystem, setSearchSystem] = useState('all')
  const [searchResults, setSearchResults] = useState<Term[]>([])
  const [selectedTerm, setSelectedTerm] = useState<Term | null>(null)
  const [loadingSearch, setLoadingSearch] = useState(false)
  const [searchFHIR, setSearchFHIR] = useState<any>(null)
  
  // Translate state
  const [translateCode, setTranslateCode] = useState('A-1')
  const [translateSystem, setTranslateSystem] = useState('Ayurveda')
  const [translationResult, setTranslationResult] = useState<any>(null)
  const [translationError, setTranslationError] = useState<string | null>(null)
  const [loadingTranslate, setLoadingTranslate] = useState(false)
  
  // Stats
  const [stats] = useState({
    ayurveda: 4124,
    siddha: 2011,
    unani: 3254,
    mappings: 9389
  })

  // Clipboard copies helper
  const [copiedText, setCopiedText] = useState<string | null>(null)
  const handleCopy = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    setCopiedText(label)
    setTimeout(() => setCopiedText(null), 1500)
  }

  // Check backend connection
  const checkConnection = useCallback(async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/`)
      if (response.ok) {
        setBackendConnected(true)
      } else {
        setBackendConnected(false)
      }
    } catch {
      setBackendConnected(false)
    }
  }, [])

  useEffect(() => {
    checkConnection()
    // Poll connection status every 10 seconds
    const interval = setInterval(checkConnection, 10000)
    return () => clearInterval(interval)
  }, [checkConnection])

  // Unified Search Handler
  const handleSearch = useCallback(async (query: string, system: string) => {
    if (!query || query.length < 2) {
      setSearchResults([])
      setSearchFHIR(null)
      return
    }

    setLoadingSearch(true)
    try {
      const systemParam = system === 'all' ? 'all' : system
      const response = await fetch(
        `${BACKEND_URL}/api/search?query=${encodeURIComponent(query)}&system=${encodeURIComponent(systemParam)}`
      )
      if (response.ok) {
        const data = await response.json()
        setSearchFHIR(data)
        
        // Map FHIR contains back to our display items
        if (data.expansion && data.expansion.contains) {
          const terms = data.expansion.contains.map((item: any) => ({
            code: item.code,
            display: item.display,
            system: item.system
          }))
          setSearchResults(terms)
        } else {
          setSearchResults([])
        }
      }
    } catch (err) {
      console.error('Search error:', err)
    } finally {
      setLoadingSearch(false)
    }
  }, [])

  // Debounced/Triggered Search
  useEffect(() => {
    const delayDebounce = setTimeout(() => {
      handleSearch(searchQuery, searchSystem)
    }, 300)

    return () => clearTimeout(delayDebounce)
  }, [searchQuery, searchSystem, handleSearch])

  // Translate Handler
  const handleTranslate = async (e?: React.FormEvent) => {
    if (e) e.preventDefault()
    if (!translateCode) return

    setLoadingTranslate(true)
    setTranslationError(null)
    setTranslationResult(null)
    
    try {
      const response = await fetch(
        `${BACKEND_URL}/fhir/ConceptMap/$translate?code=${encodeURIComponent(translateCode)}&system=${encodeURIComponent(translateSystem)}`
      )
      if (response.ok) {
        const data = await response.json()
        setTranslationResult(data)
      } else {
        setTranslationError('Code not found or translation failed.')
      }
    } catch (err) {
      setTranslationError('Could not reach backend terminology service.')
      console.error('Translation error:', err)
    } finally {
      setLoadingTranslate(false)
    }
  }

  // Load a full CodeSystem / ConceptMap payload for active inspect
  const loadResource = async (resourceName: 'CodeSystem' | 'ConceptMap') => {
    setLoadingSearch(true)
    try {
      const response = await fetch(`${BACKEND_URL}/fhir/${resourceName}`)
      if (response.ok) {
        const data = await response.json()
        setSearchFHIR(data)
        // Set searchResults empty to emphasize full resource view
        setSearchResults([])
        setSelectedTerm(null)
      }
    } catch (err) {
      console.error(err)
    } finally {
      setLoadingSearch(false)
    }
  }

  return (
    <div className="animate-fade-in">
      {/* Navigation Header */}
      <header className="navbar">
        <div className="brand">
          <Database className="brand-logo" size={28} color="#6366f1" />
          <div>
            <div className="brand-title">AyurLink</div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>
              FHIR Traditional Terminology Engine
            </div>
          </div>
        </div>

        <nav style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <div className="tabs">
            <button 
              className={`tab-btn ${activeTab === 'search' ? 'active' : ''}`}
              onClick={() => setActiveTab('search')}
            >
              <Search size={16} /> Unified Search
            </button>
            <button 
              className={`tab-btn ${activeTab === 'translate' ? 'active' : ''}`}
              onClick={() => setActiveTab('translate')}
            >
              <Shuffle size={16} /> Concept Map
            </button>
            <button 
              className={`tab-btn ${activeTab === 'explore' ? 'active' : ''}`}
              onClick={() => setActiveTab('explore')}
            >
              <Layers size={16} /> FHIR Metadata
            </button>
          </div>

          <div className={`status-badge ${backendConnected ? '' : 'disconnected'}`}>
            <span className="status-dot"></span>
            {backendConnected ? 'Connected' : 'Offline'}
          </div>
        </nav>
      </header>

      {/* Connection Warning Banner */}
      {!backendConnected && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          borderRadius: '16px',
          padding: '1rem 1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          marginBottom: '2rem',
          color: '#f87171'
        }}>
          <AlertCircle size={20} />
          <div>
            <strong style={{ display: 'block' }}>Backend Service Unreachable</strong>
            <span style={{ fontSize: '0.9rem' }}>
              Ensure your FastAPI server is running locally on port 8000. Start it with <code>uvicorn app.main:app --reload</code>.
            </span>
          </div>
        </div>
      )}

      {/* Search & Explore Tab */}
      {activeTab === 'search' && (
        <div className="dashboard-grid">
          {/* Left panel: search and list */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column' }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Search color="var(--color-accent)" size={22} /> Unified Search Console
            </h2>
            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.95rem' }}>
              Search case-insensitively across NAMASTE Ayurvedic, Siddha, Unani terminology and WHO ICD-11 codes.
            </p>

            <div className="search-controls">
              <div className="search-input-wrapper">
                <Search size={18} />
                <input 
                  type="text" 
                  className="search-input" 
                  placeholder="Enter term, code, or description (e.g. Fever, Jvara, S-10)..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              <select 
                className="system-select"
                value={searchSystem}
                onChange={(e) => setSearchSystem(e.target.value)}
              >
                <option value="all">All Systems</option>
                <option value="Ayurveda">Ayurveda (NAMASTE)</option>
                <option value="Siddha">Siddha (NAMASTE)</option>
                <option value="Unani">Unani (NAMASTE)</option>
                <option value="ICD-11-MMS">ICD-11-MMS</option>
              </select>
            </div>

            {loadingSearch && (
              <div className="empty-state">
                <div className="status-dot animate-pulse" style={{ width: '12px', height: '12px', color: 'var(--color-accent)' }}></div>
                <p>Searching FHIR Terminology Service...</p>
              </div>
            )}

            {!loadingSearch && searchResults.length === 0 && (
              <div className="empty-state">
                <HelpCircle size={48} />
                <div>
                  <p style={{ fontWeight: 500 }}>No active search results</p>
                  <p style={{ fontSize: '0.85rem', marginTop: '0.25rem' }}>
                    Type at least 2 characters to trigger live search across systems.
                  </p>
                </div>
              </div>
            )}

            {!loadingSearch && searchResults.length > 0 && (
              <div className="results-container">
                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.5rem', fontWeight: 600 }}>
                  Found {searchResults.length} ValueSet items
                </div>
                {searchResults.map((term, index) => (
                  <div 
                    key={index} 
                    className={`term-card ${selectedTerm?.code === term.code ? 'active' : ''}`}
                    style={{ borderColor: selectedTerm?.code === term.code ? 'var(--color-accent)' : 'var(--border-color)' }}
                    onClick={() => setSelectedTerm(term)}
                  >
                    <div className="term-info">
                      <div className="term-header">
                        <span className={`system-tag ${term.system.toLowerCase().includes('ayurveda') ? 'ayurveda' : term.system.toLowerCase().includes('siddha') ? 'siddha' : term.system.toLowerCase().includes('unani') ? 'unani' : 'icd11'}`}>
                          {term.system}
                        </span>
                        <span className="term-code">{term.code}</span>
                      </div>
                      <div className="term-display">{term.display}</div>
                    </div>
                    <div className="card-action">
                      <ArrowRight size={18} />
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Right panel: Detail / FHIR Raw inspect */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            {selectedTerm ? (
              <div className="glass-panel animate-fade-in" style={{ borderLeft: '4px solid var(--color-accent)' }}>
                <h3>Term Specifications</h3>
                
                <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', marginTop: '1rem' }}>
                  <div className="mapping-pair">
                    <div>
                      <span className="stat-label" style={{ fontSize: '0.7rem' }}>Clinical System</span>
                      <strong style={{ display: 'block', color: 'var(--text-primary)' }}>{selectedTerm.system}</strong>
                    </div>
                  </div>

                  <div className="mapping-pair">
                    <div>
                      <span className="stat-label" style={{ fontSize: '0.7rem' }}>Identifier Code</span>
                      <code style={{ display: 'block', marginTop: '0.25rem', color: 'var(--color-accent)' }}>{selectedTerm.code}</code>
                    </div>
                    <button 
                      onClick={() => handleCopy(selectedTerm.code, 'code')} 
                      className="tab-btn" 
                      style={{ padding: '0.4rem' }}
                    >
                      {copiedText === 'code' ? <Check size={14} color="#10b981" /> : <Copy size={14} />}
                    </button>
                  </div>

                  <div>
                    <span className="stat-label" style={{ fontSize: '0.7rem' }}>Display Name</span>
                    <p style={{ fontSize: '1.2rem', fontWeight: 600, color: '#fff', marginTop: '0.2rem' }}>
                      {selectedTerm.display}
                    </p>
                  </div>

                  {selectedTerm.translation && (
                    <div>
                      <span className="stat-label" style={{ fontSize: '0.7rem' }}>Traditional Translation</span>
                      <p style={{ color: 'var(--text-secondary)', fontStyle: 'italic', marginTop: '0.2rem' }}>
                        {selectedTerm.translation}
                      </p>
                    </div>
                  )}

                  {selectedTerm.definition && (
                    <div>
                      <span className="stat-label" style={{ fontSize: '0.7rem' }}>Clinical Definition</span>
                      <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: '1.5', marginTop: '0.2rem' }}>
                        {selectedTerm.definition}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div className="glass-panel" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '220px', color: 'var(--text-muted)' }}>
                <div style={{ textAlign: 'center' }}>
                  <HelpCircle size={32} style={{ marginBottom: '0.5rem', opacity: 0.6 }} />
                  <p style={{ fontSize: '0.9rem' }}>Select a terminology card to view clinical specifications.</p>
                </div>
              </div>
            )}

            {/* FHIR inspector */}
            <div className="glass-panel fhir-viewer">
              <div className="fhir-viewer-header">
                <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Terminal size={18} color="var(--color-accent)" /> FHIR ValueSet Inspector
                </h3>
                {searchFHIR && (
                  <button 
                    onClick={() => handleCopy(JSON.stringify(searchFHIR, null, 2), 'fhir')} 
                    className="tab-btn"
                    style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }}
                  >
                    {copiedText === 'fhir' ? 'Copied!' : 'Copy FHIR'}
                  </button>
                )}
              </div>
              {searchFHIR ? (
                <pre className="json-pre">
                  {JSON.stringify(searchFHIR, null, 2)}
                </pre>
              ) : (
                <div className="empty-state" style={{ minHeight: '200px' }}>
                  <Code size={32} />
                  <p style={{ fontSize: '0.85rem' }}>Live FHIR ValueSet JSON payloads will render here upon search queries.</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Concept Map Translator Tab */}
      {activeTab === 'translate' && (
        <div className="dashboard-grid">
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Shuffle color="var(--color-accent)" size={22} /> Traditional-to-Biomedicine Concept Mapping
            </h2>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>
              Utilize FHIR ConceptMap parameters to translate traditional NAMASTE codes directly to WHO ICD-11 codes.
            </p>

            <form onSubmit={handleTranslate} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                <div className="form-group">
                  <label>Traditional Tradition System</label>
                  <select 
                    className="input-field"
                    value={translateSystem}
                    onChange={(e) => setTranslateSystem(e.target.value)}
                  >
                    <option value="Ayurveda">Ayurveda</option>
                    <option value="Siddha">Siddha</option>
                    <option value="Unani">Unani</option>
                  </select>
                </div>

                <div className="form-group">
                  <label>NAMASTE Code</label>
                  <input 
                    type="text" 
                    className="input-field" 
                    value={translateCode}
                    onChange={(e) => setTranslateCode(e.target.value)}
                    placeholder="e.g. A-1"
                  />
                </div>
              </div>

              {/* Sample Shortcuts helper */}
              <div style={{ 
                background: 'rgba(255,255,255,0.01)', 
                border: '1px solid var(--border-color)', 
                borderRadius: '12px', 
                padding: '0.75rem 1rem' 
              }}>
                <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 600, display: 'block', marginBottom: '0.4rem' }}>
                  Quick Sample Codes:
                </span>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  <button 
                    type="button" 
                    className="tab-btn" 
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    onClick={() => { setTranslateSystem('Ayurveda'); setTranslateCode('A-1'); }}
                  >
                    Ayurveda: A-1
                  </button>
                  <button 
                    type="button" 
                    className="tab-btn" 
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    onClick={() => { setTranslateSystem('Ayurveda'); setTranslateCode('A-2'); }}
                  >
                    Ayurveda: A-2
                  </button>
                  <button 
                    type="button" 
                    className="tab-btn" 
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    onClick={() => { setTranslateSystem('Siddha'); setTranslateCode('S-1'); }}
                  >
                    Siddha: S-1
                  </button>
                  <button 
                    type="button" 
                    className="tab-btn" 
                    style={{ fontSize: '0.75rem', padding: '0.25rem 0.5rem' }}
                    onClick={() => { setTranslateSystem('Unani'); setTranslateCode('U-1'); }}
                  >
                    Unani: U-1
                  </button>
                </div>
              </div>

              <button type="submit" className="btn-primary" disabled={loadingTranslate}>
                {loadingTranslate ? 'Translating via FHIR...' : 'Query Mappings'}
              </button>
            </form>

            {/* Translation mapping flow visualizer */}
            {translationResult && (
              <div className="translator-panel animate-fade-in" style={{ marginTop: '1rem' }}>
                <h4 style={{ margin: 0 }}>Mapping Flow Visualizer</h4>
                
                <div className="interactive-flow">
                  {/* Left: Source Traditional */}
                  <div className="flow-card">
                    <div className="flow-card-header">
                      <span>Source System</span>
                      <span className="system-tag ayurveda">{translateSystem}</span>
                    </div>
                    <div style={{ textAlign: 'left', padding: '0.5rem 0' }}>
                      <code style={{ color: 'var(--color-accent)', fontSize: '1.1rem' }}>{translateCode}</code>
                      <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                        Source code querying translation map.
                      </p>
                    </div>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                      Origin CodeSystem
                    </div>
                  </div>

                  {/* Center: Mapping Relation */}
                  <div className="flow-connector">
                    <span style={{ fontSize: '0.7rem', fontWeight: 600, color: 'var(--color-accent)', textTransform: 'uppercase' }}>
                      Translate
                    </span>
                    <ArrowRight size={24} color="var(--color-accent)" />
                  </div>

                  {/* Right: Destination Biomedicine */}
                  <div className="flow-card target">
                    <div className="flow-card-header">
                      <span>Equivalent Target</span>
                      <span className="system-tag icd11">ICD-11</span>
                    </div>
                    
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', width: '100%' }}>
                      {/* Check if mappings exist */}
                      {translationResult.parameter && translationResult.parameter.some((p: any) => p.name === 'match') ? (
                        translationResult.parameter
                          .filter((p: any) => p.name === 'match')
                          .map((match: any, index: number) => {
                            const concept = match.part?.find((pt: any) => pt.name === 'concept')?.valueCoding
                            const equivalence = match.part?.find((pt: any) => pt.name === 'equivalence')?.valueCode
                            return (
                              <div key={index} style={{ 
                                background: 'rgba(99,102,241,0.08)',
                                border: '1px solid rgba(99,102,241,0.2)',
                                borderRadius: '10px',
                                padding: '0.65rem',
                                textAlign: 'left'
                              }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', marginBottom: '0.2rem' }}>
                                  <code style={{ color: '#818cf8', fontWeight: 600 }}>{concept?.code || 'N/A'}</code>
                                  <span style={{ color: 'var(--text-muted)', fontSize: '0.7rem' }}>{equivalence}</span>
                                </div>
                                <div style={{ fontSize: '0.85rem', color: '#fff', fontWeight: 500 }}>
                                  {concept?.display || 'No display text'}
                                </div>
                                <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginTop: '0.2rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                  {concept?.system}
                                </div>
                              </div>
                            )
                          })
                      ) : (
                        <div style={{ textAlign: 'center', padding: '1rem', color: 'var(--text-muted)' }}>
                          <AlertCircle size={24} style={{ display: 'block', margin: '0 auto 0.5rem', opacity: 0.5 }} />
                          <p style={{ fontSize: '0.8rem', margin: 0 }}>No matching equivalent codes in this translation map.</p>
                        </div>
                      )}
                    </div>

                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'left' }}>
                      Equivalent Clinical Mapping
                    </div>
                  </div>
                </div>
              </div>
            )}

            {translationError && (
              <div style={{
                background: 'rgba(239,68,68,0.1)',
                border: '1px solid rgba(239,68,68,0.2)',
                borderRadius: '12px',
                padding: '0.75rem 1rem',
                color: '#ef4444',
                fontSize: '0.9rem',
                textAlign: 'left'
              }}>
                {translationError}
              </div>
            )}
          </div>

          {/* Right Panel: Translation FHIR Inspector */}
          <div className="glass-panel fhir-viewer">
            <div className="fhir-viewer-header">
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Terminal size={18} color="var(--color-accent)" /> FHIR Mapping Parameters
              </h3>
              {translationResult && (
                <button 
                  onClick={() => handleCopy(JSON.stringify(translationResult, null, 2), 'fhir_params')} 
                  className="tab-btn"
                  style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }}
                >
                  {copiedText === 'fhir_params' ? 'Copied!' : 'Copy JSON'}
                </button>
              )}
            </div>
            {translationResult ? (
              <pre className="json-pre">
                {JSON.stringify(translationResult, null, 2)}
              </pre>
            ) : (
              <div className="empty-state" style={{ minHeight: '350px' }}>
                <Code size={32} />
                <p style={{ fontSize: '0.85rem' }}>Full FHIR parameter translation resource output will render here after mapping query.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* FHIR Metadata Explore Tab */}
      {activeTab === 'explore' && (
        <div className="dashboard-grid">
          {/* Metadata details */}
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
            <div>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers color="var(--color-accent)" size={22} /> FHIR Metadata resources
              </h2>
              <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', marginBottom: '1.5rem' }}>
                Explore the complete schema definitions and traditional concept maps exposed by the AyurLink terminology engine.
              </p>

              {/* Stats overview */}
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-num">{stats.ayurveda}</div>
                  <div className="stat-label">Ayurveda Terms</div>
                </div>
                <div className="stat-card">
                  <div className="stat-num">{stats.siddha}</div>
                  <div className="stat-label">Siddha Terms</div>
                </div>
                <div className="stat-card">
                  <div className="stat-num">{stats.unani}</div>
                  <div className="stat-label">Unani Terms</div>
                </div>
                <div className="stat-card">
                  <div className="stat-num">{stats.mappings}</div>
                  <div className="stat-label">Equivalent Maps</div>
                </div>
              </div>
            </div>

            {/* Quick Actions */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', borderTop: '1px solid var(--border-color)', paddingTop: '1.5rem' }}>
              <h4 style={{ margin: 0 }}>Static Schema Endpoints</h4>
              <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', margin: 0 }}>
                Query the server to load the entire dynamic CodeSystem or the unified ConceptMap mapping catalog.
              </p>
              
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '0.5rem' }}>
                <button 
                  className="tab-btn active"
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '1rem' }}
                  onClick={() => loadResource('CodeSystem')}
                >
                  <BookOpen size={20} />
                  <span>Fetch CodeSystem</span>
                  <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>/fhir/CodeSystem</span>
                </button>

                <button 
                  className="tab-btn active"
                  style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.5rem', padding: '1rem' }}
                  onClick={() => loadResource('ConceptMap')}
                >
                  <Shuffle size={20} />
                  <span>Fetch ConceptMap</span>
                  <span style={{ fontSize: '0.7rem', opacity: 0.8 }}>/fhir/ConceptMap</span>
                </button>
              </div>
            </div>
          </div>

          {/* Right Panel: Resource Viewer */}
          <div className="glass-panel fhir-viewer">
            <div className="fhir-viewer-header">
              <h3 style={{ margin: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Terminal size={18} color="var(--color-accent)" /> FHIR Schema Explorer
              </h3>
              {searchFHIR && (
                <button 
                  onClick={() => handleCopy(JSON.stringify(searchFHIR, null, 2), 'schema')} 
                  className="tab-btn"
                  style={{ fontSize: '0.8rem', padding: '0.3rem 0.75rem' }}
                >
                  {copiedText === 'schema' ? 'Copied!' : 'Copy JSON'}
                </button>
              )}
            </div>
            {searchFHIR ? (
              <pre className="json-pre">
                {JSON.stringify(searchFHIR, null, 2)}
              </pre>
            ) : (
              <div className="empty-state" style={{ minHeight: '400px' }}>
                <Code size={32} />
                <p style={{ fontSize: '0.85rem' }}>Select a schema resource action on the left to pull and inspect the full FHIR JSON schemas.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Footer */}
      <footer style={{ marginTop: 'auto', paddingTop: '3rem', paddingBottom: '1rem', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.85rem' }}>
        <p>© 2026 AyurLink Terminology Portal. Clinically aligned traditional medical indexing.</p>
      </footer>
    </div>
  )
}
