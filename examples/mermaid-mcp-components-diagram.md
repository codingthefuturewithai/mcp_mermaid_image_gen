graph TB
    subgraph "MCP Mermaid Image Gen Server"
        FastMCP[FastMCP Server]
        Tools[Tool Registration]
        Renderer[Mermaid Renderer]
        
        subgraph "Transport Modes"
            STDIO[STDIO Mode]
            SSE[SSE Mode]
        end
        
        subgraph "Tools"
            FileGen[generate_mermaid_diagram_file]
            StreamGen[generate_mermaid_diagram_stream]
        end
    end
    
    Client[MCP Client]
    MMDC[mmdc CLI]
    
    Client --> STDIO
    Client --> SSE
    
    STDIO --> FastMCP
    SSE --> FastMCP
    
    FastMCP --> Tools
    Tools --> FileGen
    Tools --> StreamGen
    
    FileGen --> Renderer
    StreamGen --> Renderer
    
    Renderer --> MMDC
    MMDC --> PNG[PNG Image]
    
    classDef primary fill:#2374ab,stroke:#2374ab,color:#fff
    classDef secondary fill:#047baa,stroke:#047baa,color:#fff
    classDef tool fill:#449dd1,stroke:#449dd1,color:#fff
    classDef external fill:#74a57f,stroke:#74a57f,color:#fff
    
    class FastMCP,Tools primary
    class STDIO,SSE secondary
    class FileGen,StreamGen tool
    class Client,MMDC,PNG external