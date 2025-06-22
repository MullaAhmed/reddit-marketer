# Reddit Marketing AI Agent - Runner Notebooks

This folder contains Jupyter notebooks that provide a complete workflow for the Reddit Marketing AI Agent. Each notebook is designed to run independently with data passed between them via JSON files.

## 📚 Notebooks Overview

### 1. `ingest_extract_discover.ipynb`
**Purpose:** Document ingestion, topic extraction, and subreddit discovery

**Workflow:**
- **Cell 1:** Ingest document content using the ingestion service
- **Cell 2:** Extract relevant topics from the ingested document
- **Cell 3:** Discover and rank subreddits based on extracted topics

**Output Files:**
- `ingested_docs.json` - Document ingestion results
- `extracted_topics_output.json` - Extracted topics
- `discovered_subreddits_output.json` - Ranked subreddits

### 2. `discover_posts_respond.ipynb`
**Purpose:** Find posts, analyze them, generate responses, and post to Reddit

**Workflow:**
- **Cell 1:** Load discovered subreddits and select targets
- **Cell 2:** Search for relevant posts in selected subreddits
- **Cell 3:** Analyze ALL discovered posts and generate responses
- **Cell 4:** Post approved responses to Reddit ⚠️

**Output Files:**
- `selected_subreddits.json` - Selected target subreddits
- `discovered_posts_output.json` - Found posts to analyze
- `generated_responses_output.json` - Generated responses
- `posted_responses_results.json` - Posting results

**⚠️ Warning:** Cell 4 will post to Reddit using your credentials!

### 3. `fetch_reddit_stats.ipynb`
**Purpose:** Fetch real-time Reddit engagement statistics

**Workflow:**
- **Cell 1:** Fetch engagement report with live Reddit data
- **Cell 2:** Get detailed posting history
- **Cell 3:** Performance analysis and recommendations

**Output Files:**
- `reddit_engagement_report.json` - Live engagement metrics
- `posting_history_report.json` - Posting history
- `performance_analysis_report.json` - Performance insights

## 🚀 Getting Started

### Prerequisites
1. Set up your `.env` file with required API keys:
   ```env
   OPENAI_API_KEY=your_openai_key
   GOOGLE_API_KEY=your_google_key
   GROQ_API_KEY=your_groq_key
   REDDIT_CLIENT_ID=your_reddit_client_id
   REDDIT_CLIENT_SECRET=your_reddit_client_secret
   REDDIT_USERNAME=your_reddit_username
   REDDIT_PASSWORD=your_reddit_password
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Workflow

1. **Start with Document Ingestion:**
   ```bash
   jupyter notebook ingest_extract_discover.ipynb
   ```
   Run all cells in sequence to ingest content, extract topics, and discover subreddits.

2. **Generate and Post Responses:**
   ```bash
   jupyter notebook discover_posts_respond.ipynb
   ```
   Run cells 1-3 to find posts and generate responses. **Be careful with Cell 4** - it posts to Reddit!

3. **Monitor Performance:**
   ```bash
   jupyter notebook fetch_reddit_stats.ipynb
   ```
   Run all cells to get real-time analytics and performance insights.

## 📁 Data Flow

```
ingest_extract_discover.ipynb
├── ingested_docs.json
├── extracted_topics_output.json
└── discovered_subreddits_output.json
    ↓
discover_posts_respond.ipynb
├── selected_subreddits.json
├── discovered_posts_output.json
├── generated_responses_output.json
└── posted_responses_results.json
    ↓
fetch_reddit_stats.ipynb
├── reddit_engagement_report.json
├── posting_history_report.json
└── performance_analysis_report.json
```

## 🔧 Key Features

### Enhanced Post Analysis
- Fetches both posts AND comments for complete context
- AI decides whether to comment on post or reply to specific comments
- Uses Haystack RAG for intelligent context retrieval

### Real-time Analytics
- Live karma scores from Reddit API
- Engagement tracking over time
- Performance recommendations

### Parallel Processing
- Concurrent subreddit discovery
- Batch document processing
- Optimized for speed and efficiency

### Safety Features
- Manual approval workflow (no automatic posting)
- Comprehensive error handling
- Rate limiting respect
- Clear warnings before posting actions

## 📊 Understanding the Output

### Engagement Metrics
- **Total Karma Earned:** Sum of all upvotes/downvotes
- **Average Karma:** Karma per response
- **Success Rate:** Percentage of successful posts
- **Response Types:** Breakdown of comment vs reply actions

### Performance Indicators
- **High Success Rate (>80%):** Excellent API connectivity
- **Good Karma (>5 avg):** Well-received responses
- **Low Karma (<1 avg):** May need response quality improvement

## 🛠️ Troubleshooting

### Common Issues

1. **"No documents found" error:**
   - Run `ingest_extract_discover.ipynb` first
   - Check if document ingestion was successful

2. **Reddit API errors:**
   - Verify credentials in `.env` file
   - Check Reddit API rate limits
   - Ensure account has posting permissions

3. **Empty subreddit discovery:**
   - Check if topics were extracted successfully
   - Verify Reddit client connectivity
   - Try broader topic keywords

4. **No posts found:**
   - Subreddits may not have relevant content
   - Try different search queries
   - Check subreddit activity levels

### Debug Tips

- Each cell saves its output to JSON files - check these for detailed error information
- Look for success/failure flags in the JSON outputs
- Check the console output for detailed error messages
- Verify all required services are properly initialized

## 🔄 Workflow Customization

### Modifying Content
Edit the `content` variable in `ingest_extract_discover.ipynb` Cell 1 to change your marketing context.

### Adjusting Search Parameters
Modify search queries and limits in `discover_posts_respond.ipynb` Cell 2.

### Changing Response Tone
Update the `tone` parameter in `discover_posts_respond.ipynb` Cell 3 (options: "helpful", "professional", "casual").

### Analytics Frequency
Run `fetch_reddit_stats.ipynb` regularly to monitor performance and engagement trends.

## 📈 Best Practices

1. **Start Small:** Begin with 2-3 subreddits and a few posts
2. **Monitor Quality:** Check generated responses before posting
3. **Respect Communities:** Ensure responses add genuine value
4. **Track Performance:** Regular analytics help optimize strategy
5. **Rate Limiting:** Allow delays between posts to respect Reddit's limits

## 🤝 Support

If you encounter issues:
1. Check the JSON output files for detailed error information
2. Verify your API credentials and permissions
3. Review the console output for specific error messages
4. Ensure all dependencies are properly installed

The notebooks are designed to be self-contained and provide clear feedback at each step of the process.