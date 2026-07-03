GenAI APAC Hackathon 
---
## **Problem Statement**


Build an AI-powered Decision Intelligence Platform that leverages data, AI models, and intelligent automation to help individuals, communities, organizations, and city stakeholders analyze information, generate insights, predict outcomes, and make better decisions that improve everyday life and community well-being.

Modern communities generate large volumes of structured and unstructured data from sources such as public services, transportation systems, environmental monitoring, healthcare systems, citizen feedback, utility networks, community programs, and digital platforms. However, transforming this information into actionable insights remains a significant challenge.

Participants are tasked with developing intelligent solutions that can understand and analyze data, answer questions in natural language, identify patterns and anomalies, generate recommendations, automate workflows, and support decision-making through AI-powered assistance.

## **Suggested Solution Areas**

Participants may address challenges related to:

- Urban mobility and transportation
- Public safety and emergency preparedness
- Healthcare access and community wellness
- Education and lifelong learning
- Environmental sustainability and climate resilience
- Waste management and resource optimization
- Energy efficiency and smart utilities
- Citizen engagement and public services
- Accessibility and inclusive communities
- Disaster response and recovery
- Tourism and local economic development
- Community support and social impact initiatives

## Technology Inspiration

Participants are encouraged to explore technologies across the Google Cloud ecosystem, including:

- Conversational analytics and natural language interfaces
- Large Language Models (LLMs) and Retrieval-Augmented Generation (RAG)
- Multimodal AI for text, image, video, and audio understanding
- Computer vision and intelligent data analytics
- Accelerated data science and machine learning workflows
- Real-time inference and scalable AI deployment
- Predictive analytics and forecasting
- Workflow automation and intelligent applications
- Responsible and explainable AI

Examples may include Vertex AI, Gemini, BigQuery, Cloud Run, Agent Development Kit (ADK), AlloyDB, Cloud Functions, Looker, and other Google Cloud services.

---


## Ideas for GenAI APAC Hackathon
1. Going from one place to other place which bus to take between the two routes, decision making, cost, speed, traffic ,ETA etc.
	  Eg : vennela wants to go to jublie hills, their are two routes and for her at a given time which route(bus/metro/cab) works best, real time traffic and customized for her timing
2. Given a fire accident in a big building situation, the trapped person might not know the path out or the actual path is blocked.
	   Pre planning of fire rescue path (for a given building or place), with video upload, creates 3 different places for best chance of rescue by fire fighters or external help	
3. Gated Communities , resource handling and issue management
		Gated communities have whatsapp groups(unstructured data) with many issues posted by users(water issues, current problems, plumbing etc) , not well tracked.
		A place where the owner or maintainer gets insights into pending works, things to do this week, planned activities for this week (niche to the gated community) 
 4. Flooding in rainy seasons or coastal areas evacuation measures and customized value addition to user to navigate the flooding.
		Take example of bengaluru in rainy seasons, roads get flooded and some communities have water blockages and related issues.
			 Normal user side : Based on the location , recommend user best possible way out of that flood or give alternate route without flooding.
			 For city management/Officials : pre flooding measures analysis via gps location/ altitude ranges, chances of flooding or water stagnation and giving recomendations on how to mitigate them before flooding(like setup a water drainage at this point , water pumps required to move water, traffic congestion analysis and ways to mitigate them etc)
		
---
## Final idea Flood-Guard AI

lets works on 1. *Flood-Guard AI* — Predictive Community Disaster Resilience Platform (Top Recommendation) , lets refine or ideate more on this , this is what i thought -  Flooding in rainy seasons or coastal areas evacuation measures and customized value addition to user to navigate the flooding.
	- Take example of Bengaluru in rainy seasons, roads get flooded and some communities have water blockages and related issues.
		 - Normal user side : Based on the location , recommend user best possible way out of that flood or give alternate route without flooding.
		- For city management/Officials : pre flooding measures analysis via gps location/ altitude ranges, chances of flooding or water stagnation and giving recommendations on how to mitigate them before flooding(like setup a water drainage at this point , water pumps required to move water, traffic congestion analysis and ways to mitigate them etc)

#### Lets plan on a full story the way of presentation

1. starting with day full of rain not yet much flooded, user asks  - Your basement is at high risk — move valuables now. Here’s checklist.
2. “I’m on a bike”, “with elderly parents”, “need to reach airport” - AI gives best navigation out possible
3. Then his wife(radha) is in home and whole colony is flooded people are stuck in home Show safe gathering points near me” or “Is my apartment society at risk?
4. Now all people are at a given safe place in community but surrounded with full flooding. - app has feature to add hostages alert points to get help to migrate.
5. City Officials /RWA - gets the alerts in real time , they have heat map of risks, which are heavily flooded, number of people available to send to rescue in team.
6. With full access to cities or places GPS , topological, drainage capacities, real time and past flooding effects , ai gives recommendations -
	1. send priority support to community (radha's signal)
	2. real time traffic diversions from flooded areas.
	3. Sending pumps or clearing drains to send out water fast.
 7. Post recovery recommendations and actions for  City Officials / RWA 
	 1. Generates ready-to-share briefs for authorities with explanations and confidence scores.
	 2. “What happens if we install a new pump at Location A?” or “Effect of desilting these 3 drains before monsoon.”
 8. Post recovery recommendations and actions for people
	 1. proactive personalized protection .
	 2. Best places to implement drains in community(need images or videos )

---


### Video demo (AI gen refined from above story)

Title Slide:  
FloodGuard AI — Predictive Community Disaster Resilience & Decision Intelligence Platform  
Saving lives and enabling smarter cities during urban floods1. Opening Hook (Problem Setup – 30-45 secs)

- Show dramatic Bengaluru rainy season footage / photos (waterlogged roads, stranded people, flooded basements).
- “Every monsoon, cities like Bengaluru face severe urban flooding. Lives are disrupted, people get stranded, and authorities struggle with reactive responses. Today, we present FloodGuard AI — an intelligent platform that shifts from reaction to proactive, personalized decision intelligence.”

2. Resident Journey – Prevention PhaseScene: Morning, heavy rain but roads still manageable.

- User (Rajesh) opens FloodGuard and asks: “How safe is my home today?”
- AI Response (Gemini-powered):  
    “Your basement is at high risk (72% probability based on altitude + forecast). Move valuables to higher floor now. Here’s your personalized 5-minute checklist.”  
    → Show generated checklist.

Demo Highlight: Conversational query + RAG over local building data.3. Navigation During Rising FloodScene: Rajesh needs to go out.

- “I’m on a bike with elderly parents and need to reach the airport.”
- AI: Analyzes real-time + predictive data → recommends safest, dry-est route with altitude-aware alternatives.  
    “Avoid ORR near Silk Board. Take this alternate route — 45 mins longer but only 8% flood risk.”

Demo Highlight: Map visualization + personalized context awareness.4. Family Emergency – Colony FloodedScene: Rajesh is away. Wife Radha is stuck at home as colony floods.

- Radha asks: “Is my apartment society at risk? Show me safe gathering points near me.”
- AI: Shows risk heatmap of the society + nearest safe elevated points.
- Multimodal moment: Radha uploads photo of rising water → AI assesses severity and triggers alert.

Demo Highlight: Multimodal understanding + community risk view.5. Community + Rescue PhaseScene: Residents move to a safe community hall but are now surrounded by water.

- Feature: “Mark Safe Spot + Distress Signal” — Residents can raise “help needed” alerts with number of people, medical needs, etc.
- System aggregates and prioritizes signals.

6. Official / RWA Dashboard – Real-time Decision IntelligenceSwitch to City Official / RWA View:

- Live heatmap: Flooded zones, number of people stranded, rescue team availability.
- AI Recommendations (Agentic intelligence):
    1. Priority Action: “Send rescue team to Radha’s community first — 47 people stranded, high vulnerability score.”
    2. Real-time traffic diversions: Suggest alternate routes for emergency vehicles.
    3. Mitigation: “Deploy 4 mobile pumps at these GPS coordinates. Clearing drains at Location B can reduce water level by 40% in 6 hours.”

Demo Highlight: What-if simulator — “What if we desilt these 3 drains?” → AI shows predicted impact with confidence score.7. Post-Flood Recovery Phase

- For Officials: Auto-generated briefing report with insights, recommended long-term actions (“Install new pump at Location A — expected 35% risk reduction”), and explanations.
- For Citizens: Personalized recovery advice — “Best places to implement community drains (with suggested locations + visual markers)”, insurance guidance, health precautions.

Closing Slide:

- Impact summary: Faster response, reduced damage, empowered decisions.
- “From reactive chaos to proactive intelligence — FloodGuard AI for resilient communities.”
- Tech stack + responsible AI note (data privacy, explainability).

---

Is this story strong? Yes — now it’s cohesive, emotional, and technically demonstrative.Quick Suggestions for Even Higher Impact

- Keep total demo under 5-6 minutes.
- Use one consistent character (Rajesh + Radha) throughout.
- End with a powerful visual: Before/After split screen.
- Mention scalability: Start with Bengaluru → expand to other APAC cities.
---
### The product requirements (Raw stuff)

- Lets plan on what all tools we will be using, algorithms to implement, data sets to collect , User interfaces to implement (simple toggle for user vs officials)  , Backend architecture, AI architecture (multi-agent) - all of this  via which platforms(prefer the one hackathon gave)
- This is what i think it is 
	1. Tools we need - 1. Real time weather data(API, it includes where rain is happening severity etc. ), historical events of floods in that area(rag or vector search in db), GPS and topographic features of that area , knowledge on what kind of area is it(more residentials type, city flyovers, most happening place, park etc. ) , google maps API (custom route creation rather than google maps normal routes) , multimodality, local guidelines of disasters if any.
	based on what we both thank, i have few questions too
	2. you mentioned checklist , what can it be, give a full example of location aware guidance and navigation guidance.

	frontend - web app React JS, orchestration ADK , gemini 3.5 flash  and lite, Firestore for vectors+vertex ai vector search 
	
	Things i want to understand
	1. Thinking all tools to be written as MCP's
	2. Tools top level - 
		1. The tools will have a parameter wherever possible to have mock vs real time (especially for weather,  topologies and navigations)
		2. weather, elevation/topology, historical data/floods , maps/navigation creation(1) ,current location of user ,  Google maps/google grounding for location specific images and place info(2) , Alert triggers,  visualization of maps (with heat map layer, triggered alert layer, Pumps locations, drainage points etc,) , rescue  algo , traffic diversion and recommendation systems
			1. How to create custom navigation routes and they start  should use the shared navigation rather than Shortest path google recommends (what are the inputs and what outputs i get and how to show them)
			2. For a user asking am i safe from an apartment, get user location, user uploaded image/video (if any), gets apartment name or location and images from google maps , analysis terrain and gives overall conclusion , and info about the apartment or locality also works
	3. The officials have access to visualize past flooding events, risk profiles, topological layer, Alert triggered points, Drains, Support people location, water pump's etc.
	4. Should we have toggle for user/official or two different interfaces is best ? (even in toggle, the things should be independent)
	5. Both the interfaces have a templated questions , clickable to directly send to ai
	6. We are only showing maps in dashboard for officials, for users , a link to google maps is provided vs Using A2UI for both sides visual renderings.

 - [ ] Yet to complete the Design doc with MCP Tools schema, DB schemas, agent design stuff
 - [ ] Setup Infra for LLM, ADK, Big query, vector search and storage
 - [ ] Collect and curate the mock and real world data and upload to the vector DB / Big Query
 - [ ] Boiler plates for and interfacing with the frontend for backend
 - [ ] write prompts for each agent , and integrating tools(including search and ML algo's)
 - [ ] Test and iterate the full flow
 - [ ] Create PPT, video Demo , production URL, Github repo - deadline - 06/07/2026 11:59:00 PM(IST)
---
## Few test cases

- Radha asks: “Is my apartment society at risk? Show me safe gathering points near me.”  - The ai check GPS , gets her apartment images from maps or somewhere, analysis with all Realtime data and gives recommendation.
- you mentioned checklist , what can it be, give a full example of location aware guidance and navigation guidance.