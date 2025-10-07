# 🚀 AI Data Assistant (Gemini & Streamlit)

An interactive **AI-powered data assistant** built with **Streamlit** and **Docker**.  
It allows you to:

- Generate **synthetic data** based on your database schema (DDL).
- Interact with the data using **natural language queries** that are automatically translated into SQL.
- Visualize, edit, and persist the generated data in a **PostgreSQL database**.

---

## ✨ Key Features

### 1. 🛠️ Data Generation

- 📥 **Schema Upload:** Upload a `.sql` file containing `CREATE TABLE` statements.
- 🤖 **AI-Powered Generation:** Uses **Google Gemini 2.5 Flash** to generate realistic synthetic data that conforms to your schema.
- ⚙️ **Customization:** Adjust model creativity (**temperature**), set **max tokens**, and add custom **prompt instructions**.
- 📊 **Visualization & Editing:**
  - Preview generated data in interactive tables.
  - Manually edit data directly in the app.
  - Use **“Quick Modifications”** with natural language commands to edit data via AI.
- 💾 **Persistence:** Automatically inserts generated data into a **PostgreSQL** database.
- 📥 **Download:** Export all generated data as a **ZIP file**.

---

### 2. 💬 Talk to Your Data (NL → SQL)

- 💻 **Conversational Interface:** Ask questions in Spanish or English about your data.
- 🔀 **SQL Translation:** Uses Gemini to convert natural language queries into SQL.
- ⚡ **Execution & Results:** Runs the SQL queries on PostgreSQL and shows clean, tabular results.
- 🕵️ **Observability:** Integrated with **Langfuse** to trace and debug NL→SQL interactions.

---

## 🖥️ Tech Stack

| Layer         | Technology                                         |
| ------------- | -------------------------------------------------- |
| Frontend      | [Streamlit](https://streamlit.io/)                 |
| Backend       | Python                                             |
| AI Model      | Google Gemini 2.5 Flash                            |
| Database      | PostgreSQL                                         |
| Container     | Docker & Docker Compose                            |
| Observability | Langfuse                                           |
| Main Libs     | `pandas`, `psycopg2-binary`, `google-generativeai` |

---

## ⚙️ Prerequisites

- 🐳 **Docker & Docker Compose** installed on your machine.
- 🔑 **Google API Key** for Gemini (get it from [Google AI Studio](https://aistudio.google.com/)).
- 📈 _(Optional)_ **Langfuse** credentials for observability.

---

## 🚀 Installation & Startup

Follow these steps to get the project running locally:

### 1. 📂 Clone the Repository

```bash
git clone <URL_OF_YOUR_REPOSITORY>
cd <FOLDER_NAME>
```

---

### 2. ⚙️ Create the Environment File

Create a `.env` file in the project root with the following content (replace placeholders with your actual credentials):

```env
# PostgreSQL Database
DB_NAME=my_database
DB_USER=my_user
DB_PASS=my_password

# Google Gemini API Key
GOOGLE_API_KEY=your_google_api_key

# (Optional) Langfuse for observability
LANGFUSE_PUBLIC_KEY=pk-lf-xxxxxxxxxxxxxxxxxxxxxxxx
LANGFUSE_SECRET_KEY=sk-lf-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

---

### 3. 🐳 Run with Docker Compose

In the project root, run:

```bash
docker compose up -d --build
```

Flags:

- `-d`: Runs containers in the background.
- `--build`: Rebuilds the app image to apply code changes.

---

### 4. 🌐 Access the Application

Once containers are running, open your browser at:

```
http://localhost:8501
```

---

## 📚 How to Use

### ▶️ **Data Generation Tab**

1. Upload a `.sql` file with your DDL schema.
2. (Optional) Add a custom prompt to guide data generation.
3. Adjust **Temperature** or **Max Tokens** as needed.
4. Click **Generate** to create and load data into the database.
5. Preview, manually edit, or use AI to modify the generated data.

---

### 💬 **Talk to Your Data Tab**

1. Switch to the **“Talk to your data”** tab.
2. Type a question about your data (e.g., _"What is the most expensive product?"_).
3. The system:
   - Translates your question into SQL.
   - Executes the query.
   - Displays the result in a table.

---

## 📦 Project Structure (Simplified)

```
AI-Data-Assistant/
├─ app.py                # Main Streamlit application
├─ genai_data.py         # Functions for data generation
├─ docker-compose.yml    # Container orchestration
├─ Dockerfile            # App image definition
├─ requirements.txt      # Python dependencies
├─ .env                  # Environment variables
└─ README.md             # Project documentation
```

---
