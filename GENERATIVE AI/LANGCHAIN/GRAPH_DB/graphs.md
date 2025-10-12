## Knowledge Graphs (KGs)

A **Knowledge Graph (KG)** is a **semantic network of real-world entities** — such as people, places, events, or concepts — that captures **relationships between them**.

---

### 🧩 Key Components

1. **Nodes** – Represent entities like a person, place, object, or concept.  
   *Example:* `Rohit Sharma`, `Virat Kohli`, `Indian Cricket Team`

2. **Edges** – Define the **relationship** between nodes.  
   *Example:* `is captain of`, `is player of`

3. **Labels** – Indicate the **type or role** of nodes and edges.  
   *Example:* Node labels – `Person`, `Team`; Edge labels – `captain of`, `player of`

---

### ⚙️ Example

| Entity 1        | Relationship     | Entity 2             |
|-----------------|------------------|----------------------|
| Rohit Sharma    | is captain of    | Indian Cricket Team  |
| Virat Kohli     | is player of     | Indian Cricket Team  |

**Question:** What is the relationship between Rohit Sharma and Virat Kohli?  
**Answer:** Both are connected to the same team (`Indian Cricket Team`) with different roles — one as **captain**, the other as **player**.

---

### 🌍 Real-World Use

- Knowledge Graphs power intelligent systems like **Google Search** to understand entity relationships.  
- They enable **semantic reasoning** beyond basic keyword matching.

---

### 🧠 Summary

Knowledge Graphs = **Nodes + Edges + Labels**

They model entities and their relationships to help machines **reason about the real world** in a structured, interconnected way.

---

## RDBMS vs Graph Databases

| Concept                     | RDBMS (Relational)        | Graph Database (e.g., Neo4j)       |
|-----------------------------|----------------------------|------------------------------------|
| Structure                   | Tables                     | Graphs                             |
| Data Representation          | Rows (records)             | Nodes                              |
| Attributes                   | Columns and data           | Properties and values              |
| Relationships                | Constraints (PK, FK)       | Explicit relationships (edges)     |
| Query Mechanism              | Joins in SQL               | Traversals in Cypher               |

---

### ⚡ Advantages of Neo4j

1. **Graph Data Model** – Represents data as nodes, relationships, properties, and values.  
2. **Real-Time Insights** – Enables instant relationship-based queries.  
3. **Easy Retrieval** – Uses **Cypher Query Language** for intuitive, visual querying.  
4. **No Joins Needed** – Relationships are directly stored and traversed.  
5. **ACID Compliance** – Ensures Atomicity, Consistency, Isolation, and Durability.  
6. **Flexible Schema** – Allows dynamic data modeling without rigid table structures.

---

## 🧩 Neo4j Property Graph Data Model

The **Neo4j Graph Database** is based on the **Property Graph Model**, which is used to **store and manage data** in a connected form.

Neo4j Graph DB
↓
Property Graph Model
↓
Data Model = { 1. Nodes, 2. Relationships, 3. Properties }

- **Nodes** – Represent entities.  
- **Relationships** – Represent directed connections between nodes (can be **uni** or **bi-directional**).  
- **Properties** – Store metadata as **key–value pairs** for nodes and relationships.

**Example Visualization:**

START Node (node1) ── parentOf ──► END Node (node2)

---

### 🧠 NLP + Graph Neural Networks

In **NLP applications**, graph-based reasoning is used internally through **Graph Neural Networks (GNNs)**.  
When integrated with **LangChain**, such models leverage KGs to perform **contextual understanding, reasoning, and retrieval** across entities.

---


# Introduction to Cypher with Sydney Sweeney Example

Cypher is the query language for **Neo4j**, a graph database. It allows you to create, read, update, and delete **nodes** (entities) and **relationships** (connections between entities). Graph databases are ideal for representing relationships like actors and the movies they acted in.

---

## 1️⃣ Basics of Cypher

- **Nodes** are represented by parentheses `( )`.  
- **Relationships** are represented by square brackets `[ ]` and arrows `->`.  
- **Labels** categorize nodes, e.g., `Actor` or `Movie`.  
- **Properties** are key-value pairs inside `{ }`.  
- **MATCH** is used to find nodes or relationships.  
- **CREATE** is used to make new nodes or relationships.  

Example:  
```cypher
CREATE (Sydney:Actor {name: "Sydney Sweeney", dob: "1997-09-12"});
```

This creates a node with label Actor and properties name and dob.


## 2️⃣ Creating Nodes, Labels, and Properties

- Sydney → variable name to reference this node later.

- :Actor → label indicating the type of node.

- {name: "Sydney Sweeney", dob: "1997-09-12"} → properties storing information about the actor.

## Creating Movie Nodes
```cypher
CREATE (Euphoria:Movie {
  title: "Euphoria",
  released: 2019,
  genre: "Drama"
});

CREATE (EverythingEverywhere:Movie {
  title: "Everything Everywhere All at Once",
  released: 2022,
  genre: "Sci-Fi"
});
```

- Euphoria and EverythingEverywhere → variable names.

- :Movie → label for movie nodes.

- Properties like title, released, and genre describe the movies.

## 3️⃣ Creating Relationships

Actor to Movie Relationship
```cypher
CREATE (Sydney)-[:ACTED_IN]->(Euphoria);
CREATE (Sydney)-[:ACTED_IN]->(EverythingEverywhere);
```
- (Sydney) → actor node.

- -[:ACTED_IN]-> → relationship type with direction.

- (Euphoria) → movie node.
This represents that Sydney Sweeney acted in these movies.

## Connecting Another Actor to the Same Movies
```cypher
CREATE (John:Actor {name: "John Doe", dob: "1990-05-15"});

MATCH (Sydney:Actor {name: "Sydney Sweeney"})-[:ACTED_IN]->(m:Movie)
CREATE (John)-[:ACTED_IN]->(m);
```

- Creates a new actor John Doe.

- Finds all movies Sydney Sweeney acted in.

- Connects John Doe to the same movies using ACTED_IN.
This allows multiple actors to be related to the same movie node, showing co-acting relationships.

## 4️⃣ Querying the Graph
To see all movies an actor has acted in:
```cypher
MATCH (Sydney:Actor {name: "Sydney Sweeney"})-[:ACTED_IN]->(m:Movie)
RETURN Sydney.name AS Actor, m.title AS Movie, m.released AS Year, m.genre AS Genre;
```

5️⃣ Updating Nodes and Relationships

Update Node Properties

```cypher
MATCH (Sydney:Actor {name: "Sydney Sweeney"})
SET Sydney.dob = "1997-09-11"
RETURN Sydney;
```
- MATCH finds the node.

- SET updates the property (dob) of the node.

Update Relationship Properties
```cypher
MATCH (Sydney:Actor {name: "Sydney Sweeney"})-[r:ACTED_IN]->(m:Movie {title: "Euphoria"})
SET r.role = "Lead Actress"
RETURN r;
```
- Adds a new property role to the ACTED_IN relationship.

## 6️⃣ Deleting Nodes and Relationships

Delete a Relationship
```cypher
MATCH (Sydney:Actor)-[r:ACTED_IN]->(m:Movie {title: "Euphoria"})
DELETE r;
```
Delete a Node (with all its relationships)
```cypher
MATCH (Sydney:Actor {name: "Sydney Sweeney"})
DETACH DELETE Sydney;
```


