```mermaid
graph TD
    %% ISP Fiber Network Hierarchy
    
    LCP[LCP - Local Convergence Point<br/>Coverage: 1km radius<br/>Location: Barangay Level]
    
    LCP --> SP1[Splitter 1:8<br/>8 output ports]
    LCP --> SP2[Splitter 1:16<br/>16 output ports]
    LCP --> SP3[Splitter 1:32<br/>32 output ports]
    
    SP1 -->|Port 1| NAP1[NAP-001<br/>8 customer ports]
    SP1 -->|Port 2| NAP2[NAP-002<br/>16 customer ports]
    SP1 -->|Port 3| NAP3[NAP-003<br/>8 customer ports]
    SP1 -->|Port 3| NAP4[NAP-004<br/>4 customer ports<br/>Cascaded with NAP-003]
    
    SP2 -->|Port 1| NAP5[NAP-005<br/>8 customer ports]
    SP2 -->|Port 2| NAP6[NAP-006<br/>8 customer ports]
    
    NAP1 --> P1[Customer Ports<br/>P1-P8]
    NAP2 --> P2[Customer Ports<br/>P1-P16]
    NAP3 --> P3[Customer Ports<br/>P1-P8]
    
    P1 -->|Port 1| C1[Customer 1<br/>House/Business]
    P1 -->|Port 2| C2[Customer 2<br/>House/Business]
    P1 -->|Port 3| C3[Customer 3<br/>House/Business]
    
    classDef lcpClass fill:#dc2626,stroke:#991b1b,color:white
    classDef splitterClass fill:#f59e0b,stroke:#d97706,color:white
    classDef napClass fill:#3b82f6,stroke:#2563eb,color:white
    classDef portClass fill:#10b981,stroke:#059669,color:white
    classDef customerClass fill:#8b5cf6,stroke:#7c3aed,color:white
    
    class LCP lcpClass
    class SP1,SP2,SP3 splitterClass
    class NAP1,NAP2,NAP3,NAP4,NAP5,NAP6 napClass
    class P1,P2,P3 portClass
    class C1,C2,C3 customerClass
```

## Network Capacity Calculation Example

### Given:
- 1 LCP with 3 Splitters
  - Splitter 1: Type 1:8 (8 ports)
  - Splitter 2: Type 1:16 (16 ports)
  - Splitter 3: Type 1:32 (32 ports)
- Total Splitter Ports: 8 + 16 + 32 = 56 ports

### If each splitter port connects to NAPs:
- Average NAP has 8 customer ports
- Total Customer Capacity: 56 × 8 = 448 customers

### Real-World Distribution:
- High-density areas: Use 1:32 or 1:64 splitters
- Medium-density: Use 1:16 splitters
- Low-density/Rural: Use 1:4 or 1:8 splitters

### Port Assignment Rules:
1. One NAP port = One customer location
2. Multiple NAPs can share same splitter port (cascading)
3. Each customer gets exclusive port access
4. Unused ports remain available for expansion
