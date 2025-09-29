import os
from crewai import Task
from datetime import datetime

class NewsTasks:
    
    def __init__(self):
        os.makedirs("outputs", exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_date = datetime.now().strftime("%B %d, %Y at %I:%M %p IST")
    
    def research_news_task(self, agent, topic: str) -> Task:
        return Task(
            description=f"""
            Research recent news about: {topic}
            
            🚨 **CRITICAL REQUIREMENT: ALWAYS MENTION DATES & TIMESTAMPS!** 🚨
            
            For EVERY article and piece of information you find, you MUST include:
            - **Exact publication date** of each article (e.g., "September 28, 2025")
            - **Time relevance** (e.g., "2 hours ago", "yesterday", "this morning", "breaking news")
            - **Timestamp context** (e.g., "published at 3:45 PM", "updated 30 minutes ago")
            - **Recency indicators** (e.g., "🔥 BREAKING", "⚡ JUST IN", "📈 TRENDING NOW")
            
            **Your Research Mission:**
            1. 🔍 **HUNT FOR BREAKING NEWS** - Focus on last 24-48 hours first
            2. 📰 **CAPTURE HEADLINES** - Get catchy, attention-grabbing titles
            3. ⏰ **TIME-STAMP EVERYTHING** - When was each piece of news published?
            4. 🌍 **MULTI-SOURCE VERIFICATION** - Cross-check across different news outlets
            5. 📊 **GATHER FRESH DATA** - Look for latest statistics and numbers
            6. 💬 **EXPERT SOUNDBITES** - Find recent quotes and expert opinions
            
            **Quality Check:**
            - Is this news from today/yesterday? ✅
            - Do I have exact publication times? ✅
            - Are my sources clearly dated? ✅
            - Have I indicated how "fresh" this news is? ✅
            
            Make your research feel URGENT and CURRENT - like you're a breaking news reporter!
            """,
            agent=agent,
            expected_output=f"""
            # 📊 BREAKING NEWS RESEARCH REPORT
            ## {topic.upper()} - LATEST INTEL
            
            ---
            **🕐 Research Compiled:** {self.current_date}  
            **📍 Research Status:** LIVE & UPDATING  
            **⚡ Urgency Level:** HIGH PRIORITY  
            ---
            
            ## 🔥 BREAKING NEWS ALERTS
            *Most recent developments (last 24 hours)*
            
            ### ⚡ **JUST IN** - [Time: XX:XX AM/PM]
            - **HEADLINE:** [Attention-grabbing news headline]
            - **📅 WHEN:** [Exact date + time published]
            - **📰 SOURCE:** [News outlet name]
            - **🎯 IMPACT:** [Why this matters right now]
            - **📊 KEY NUMBERS:** [Any statistics mentioned]
            
            ### 📈 **TRENDING NOW** - [Time: XX:XX AM/PM]  
            - **HEADLINE:** [Another major development]
            - **📅 WHEN:** [Publication timestamp]
            - **📰 SOURCE:** [Media source]
            - **💡 INSIGHT:** [What experts are saying]
            
            ---
            
            ## 📰 TODAY'S TOP STORIES
            *Breaking developments from the past 48 hours*
            
            | **🕒 TIME** | **📰 HEADLINE** | **🌐 SOURCE** | **⚡ STATUS** |
            |-------------|-----------------|----------------|----------------|
            | 2:45 PM Today | [Compelling headline] | [News source] | 🔥 BREAKING |
            | 11:30 AM Today | [Important update] | [Media outlet] | 📈 TRENDING |
            | Yesterday 8:00 PM | [Recent development] | [News agency] | ⏰ RECENT |
            
            ## 🎯 QUICK FACTS & FIGURES
            *Latest data and statistics with timestamps*
            
            - **📊 KEY STATISTIC:** [Number/percentage] *(Source: [Outlet], Published: [Date/Time])*
            - **💰 MARKET IMPACT:** [Financial data] *(As of: [Timestamp])*  
            - **📈 GROWTH RATE:** [Percentage] *(Latest report: [Date])*
            
            ## 💬 WHAT THE EXPERTS SAY
            *Recent quotes and analysis*
            
            > **"[Expert quote here]"**  
            > — *[Expert Name], [Title] | Quoted in [Source] on [Date at Time]*
            
            > **"[Another important quote]"**  
            > — *[Another Expert], [Position] | [Publication] - [Timestamp]*
            
            ## ⚠️ DEVELOPING STORIES TO WATCH
            *Stories that are still evolving*
            
            - 🔄 **[Ongoing story headline]** - *Last updated: [Time]*
            - 👁️ **[Developing situation]** - *Breaking: [Recent timestamp]*
            - 🎯 **[Emerging trend]** - *First reported: [Date/Time]*
            
            ---
            **📝 RESEARCH NOTES:** All timestamps verified | Sources cross-checked | Data current as of {self.current_date}
            """,
            output_file=f"outputs/{topic.replace(' ', '_').lower()}_research_{self.timestamp}.md"
        )
    
    def write_news_report_task(self, agent, topic: str) -> Task:
        return Task(
            description=f"""
            Create a STUNNING newspaper-style article about: {topic}
            
            **🎨 CREATIVE WRITING REQUIREMENTS:**
            
            📰 **NEWSPAPER STYLE MANDATE:**
            - Write like a TOP newspaper editor - punchy, engaging, informative
            - Use creative headlines that GRAB attention (think New York Times meets Buzzfeed)
            - Include dramatic markdown formatting - **bold**, *italics*, `highlights`
            - Add visual elements: emojis, lines, boxes, tables
            - Make it scannable with bullet points and short paragraphs
            
            ⏰ **DATE & TIME OBSESSION:**
            - Mention EXACT dates and times throughout the article
            - Use phrases like "As of [time]", "Breaking at [timestamp]", "Updated [time]"
            - Include "WHEN IT HAPPENED" timeline sections
            - Add "LATEST UPDATE:" sections with timestamps
            
            🎯 **FORMATTING MAGIC:**
            - Use `---` for dramatic dividers
            - Create quote boxes with `>`
            - Make important facts **BOLD**
            - Use tables for comparisons
            - Add status badges like 🔥 BREAKING, ⚡ URGENT, 📈 TRENDING
            
            📖 **READABILITY GOALS:**
            - Write for busy people who scan quickly  
            - Use short paragraphs (2-3 sentences max)
            - Include numbered lists and bullet points
            - Add summary boxes and quick facts
            - Make key information jump off the page
            
            Think: "How would I write this if it was going on the FRONT PAGE of tomorrow's newspaper?"
            """,
            agent=agent,
            expected_output=f"""
            # 📰 THE DAILY TECH TRIBUNE
            ## 🚨 SPECIAL EDITION - {topic.upper()}
            
            ---
            **📅 PUBLICATION DATE:** {self.current_date}  
            **⚡ BREAKING NEWS STATUS:** ACTIVE  
            **👥 IMPACT LEVEL:** WIDESPREAD  
            ---
            
            # 🔥 [DRAMATIC HEADLINE THAT GRABS ATTENTION]
            ## *Subtitle that adds crucial context and urgency*
            
            ### ⚡ **LATEST UPDATE:** [Current Time] - [Brief urgent update]
            
            ---
            
            ## 📍 **THE STORY AT A GLANCE**
            
            | **📊 WHAT** | **⏰ WHEN** | **🌍 WHERE** | **💥 IMPACT** |
            |-------------|-------------|---------------|----------------|
            | [Key event] | [Exact time] | [Location] | [Significance] |
            | [Major development] | [Timestamp] | [Region] | [Effect] |
            
            ---
            
            ## 🎯 **BREAKING DEVELOPMENTS**
            
            **🕐 [Time] - JUST IN:** [Latest development here]
            
            The situation unfolded rapidly when [specific event] occurred at **exactly [time]** this [morning/afternoon/evening]. According to sources close to the matter...
            
            > **"[Compelling quote]"**  
            > — *[Source name], speaking to reporters at [time]*
            
            ### ⚡ **TIMELINE OF EVENTS**
            
            - **🕘 [Time]:** [First event happens]
            - **🕙 [Time]:** [Second major development]  
            - **🕚 [Time]:** [Current situation]
            - **🕛 [Upcoming]:** [What to expect next]
            
            ---
            
            ## 📊 **BY THE NUMBERS**
            *Latest statistics and data*
            
            - **💰 [Financial Impact]:** `$[Amount]` *(as of [timestamp])*
            - **📈 [Growth Rate]:** `[Percentage]%` *(measured at [time])*
            - **👥 [People Affected]:** `[Number]` *(count from [date])*
            
            ---
            
            ## 💬 **WHAT PEOPLE ARE SAYING**
            
            ### 🎤 **Expert Analysis**
            
            > **"[Expert opinion with impact]"**  
            > — *Dr. [Name], [Title] | Interview conducted [date] at [time]*
            
            ### 📱 **Social Media Buzz**
            
            The hashtag #[RelevantHashtag] began trending at **[time]** with over **[number]** posts in the first hour...
            
            ---
            
            ## 🔮 **WHAT HAPPENS NEXT?**
            
            ### ⏰ **IMMEDIATE FUTURE** *(Next 24 Hours)*
            - [ ] **[Expected development]** - *Expected: [date/time]*
            - [ ] **[Another milestone]** - *Scheduled: [timestamp]*
            
            ### 📅 **UPCOMING MILESTONES**
            - **[Date]:** [Important event coming up]
            - **[Future date]:** [Longer-term implication]
            
            ---
            
            ## 🎯 **KEY TAKEAWAYS**
            
            #### ✅ **What We Know For Sure:**
            - [Confirmed fact with timestamp]
            - [Verified information with date]
            - [Solid evidence with time reference]
            
            #### ❓ **What We're Still Watching:**
            - [Developing story element]
            - [Unconfirmed reports to track]
            - [Questions still being answered]
            
            ---
            
            ## 📞 **STAY UPDATED**
            
            🔔 **This story is developing...** Last updated at **{self.current_date}**
            
            > **Editor's Note:** This report will be updated as new information becomes available. All timestamps are in IST unless otherwise noted.
            
            ---
            **📰 THE DAILY TECH TRIBUNE** | *Your Source for Breaking Tech News*  
            **📧 NEWSROOM** | *Published: {self.current_date}*
            """,
            context=[],  # Will be set to research task
            output_file=f"outputs/{topic.replace(' ', '_').lower()}_final_report_{self.timestamp}.md"
        )
