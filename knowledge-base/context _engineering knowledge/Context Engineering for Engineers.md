# Context Engineering for Engineers

https://www.youtube.com/watch?v=3jN77Aw7Utk

## Introduction to Context Engineering

So tonight, I want to share some thoughts about Context Engineering for Engineers, this audience. By way of context, my name is Jeff, and I'm the founder of Chroma. Chroma for those of you who don't know, builds a search and retrieval database. Numerous illustrious speakers have shouted out at Chroma, so thank you very much. But let's get into some

## Understanding AI Systems as Programs

So I will assert, Jake and I can get into Fisticuffs later on this, but I will assert that Context Engineering is a much better term than prompt engineering or rag. I think there's a lot of buzzwords that fly around in the AI space and every week there's some new AI thought boy with their head explode emoji going crazy over some new technique. They tell you the 18 different kinds of rag that you need to know about to stop. Mute them, your life will be better. And I think as evidenced by a lot of the things you for tonight that's very true.

## The Concept of Context Engineering & Building Reliable Software with AI

Introduction to Context Engineering So, what is our shared goal?

Our shared goal is to build reliable software. This new software has some new abilities and primitives that prior software didn't. That can be pretty useful. We believe AI can be useful if you give it the right context and these systems ideally are reliable, fast and cheap. I do believe that in general we should all take a make it work, make it fast, make it cheap, type approach, and probably today most people are still on stage one. How do we make it reliable?

## Challenges with Long Contexts & Chroma's Technical Report Insights

Why don't we just use Long Context? We don't know yet but as the room is full of engineers and builders we want to know what works today.

So Chroma put out this Technical Report about a month ago, Kelly who did a lot of the work on this is in the audience, shout out Kelly. And yeah this video now has done about 120,000 views on YouTube so it is doing pretty well. And what we should demonstrate in this Technical Report is this across simple tasks that you think a human should do pretty well. This is a task to repeat back certain set of words.

Model Performance as an input of token length goes down precipitously. It is clipping off the bottom here but I'll tell you I believe that the blue dot at the far bottom of my hand corner is 10,000 tokens.

So actually model performance, I've heard a couple of the numbers reference tonight 40% 170K across some tasks seems like it's even much much sooner than that.

## Needle in a Haystack Problem

Now, of course, the way that usually the labs substantiate these Context Windows being useful is to tell you about Needle in a Haystack.

Needle in a Haystack is solved across all the different token dimensions. Great. But I think what we want to point out to people is Needle in a Haystack is a very easy task. On the screen I have an example of both a Needle and a Haystack. And you'll notice that there's number one, the model only has to pay attention to a Needle by definition. It doesn't have to pay attention to lots of the Context Windows. Only the Needle and the number two, the reasoning power is basically zero. I will read this out loud.

The question is, what was the best writing advice I got from my college classmate?

The Needle is the best writing advice I got from my college classmate was to write every week. So imagine the reasoning power required to make that match is basically zero. And what we ended up doing was plotting a number of different tasks across these dimensions of on the left hand axis amount. So the amount of the Context window of the model has to pay attention. And then the bottom axis is the difficulty or the reasoning power required to do this task well. And you'll notice Needle in a Haystack is on the bottom left requires you to pay attention to a Needle, zero reasoning power.

## The Importance of Context in AI Tasks & Gather and Glean Model

The most interesting things people are doing at Language Models today require either more context or reasoning or both, and actually many agent tasks and summarization are much more difficult. And so then it sort of begs the question, well, how much of the model can you actually use effectively? So we also ran some tests on long ran e-vow and demonstrated that very simply if you were to give the model full context versus focus context, focus context in this case is oracle, so it's sort of human curated. This is the numbers for performance, so we get massive gains in performance by curating context. You should curate your context. So probably speaking of the goal of context engineering is to number one, find the relevant information, number two, remove the irrelevant information, and then number three, optimize the relevant information. And you can argue that for any given turn of the model, there's this problem of, out of all the information in the universe, what information should be in the context window this time. And I have the model here that I call gather and glean.

Yes, it is in a iteration. Yes, I did think about that for probably 30 minutes to get there. And the way that I think makes sense to think about this problem is for those of you who have a machine learning background, this will connect, if not, I'll explain it again. Stage one is you want to maximize recall. You want to get all possible relevant tokens or information, even at the risk of getting information that's not relevant. And then stage two is maximizing precision. You want to then remove and call out and cut out all the irrelevant information. So you're just left with that pristine set of highly relevant non-destracting information.

## Data Gathering Techniques & Gleaning and Optimizing Data

We're seeing a lot of developers do now on the retrieval side as this very interesting pipeline where the query comes in from the user. You have an LLM create functionally a query plan of like, okay, based on this query I'm going to use these tools. I'm going to search in these ways. Maybe it creates 10 different search probes or 30 different search probes across structured data, SQL queries, APIs and tools on structured data like data in Chroma, and it gets a big pool of data.

And then there's a question of like, well how do you glean it down? And I'm going to get to that in a second.

So again gathering is not news to you all, but you know it could be structured data, unstructured data, local file system tools, other kinds of tools against CP tools, web search, your chat conversation history, you know all these pools of data may be relevant to the task the model has at hand.

And then Glean, so top K on vector similarity, I think you've seen that mentioned before, that's usually people's first pass. The next sort of approach to you people use commonly is reciprocal rank fusion or RF, LTR, learning to rank as sort of an OG information retrieval technique that's implemented into a last search. And then of course you have dedicated re-ranking models, also common, and then increasingly just LLMs, believe it or not, LLM, this is a great meme. And what I think is quite interesting is actually that more and more developers that I talk to are, they're calling it cheating at search or brute forcing search. Instead of trying to get super fancy about it, they're just using more intelligence, like spend more money on tokens. You don't have to use save-of-the-art models all the time, you can use small fast sheet models, and use a lot of them in parallel to kind of help you with this curation and gleaning stage.

## Content Engineering for Agents

All right, so now I want to spend a little bit more time talking about Context Engineering for Agents. And of course, what is Agents? Well, there's a loop happening here. And so, you know, in a deep research agent, for example, you're not just doing this gather and glean task once. You're doing this gather and glean task many times, conceptually. You're doing it inside of sub-agents and the sub-agents are getting judged by the orchestrator and they're going back and forth and, you know, carving up the web and finding lots of relevant information. And so, of course, this makes this stuff more complicated and more interesting. And, you know, notably, you now have the addition of agent conversation in history as a major factor in the context window, when you're going back and forth, you're generating lots of information. This was also alluded to a moment ago, but Proctestories can be really, really big. So, for example, this is a GIF, and it's a little bit blurry, but this is an example from a sweet bench of like the code and logs generated from like one, you know, a couple of terms of sweet bench. Like, as I've been stated before, you know, what human could possibly parse this and make sense of that is insanely large. And so, we really found this quite interesting learning, actually, when we were looking at the ability of agents to learn from long contours.

## Challenges with Agent Performance & The Role of Compaction

We found one thing that was quite notable, which was that if you give the Agent access to past failure cases, it helps improve agent performance. The agent seems to be able to break out of these local minimas where it commonly gets trapped and move forward, but it wasn't really a slam dunk to give the Agent access to prior success cases. I think this is why it's important to create a community around this idea of Conext Engineering so we can all solve these problems together.

Compaction is a really important point of leverage, understanding that gift that I showed you a moment ago that's going on forever and ever and ever.

How do you distill down for the next turn of the model?

Compaction is so important. What you find is that today's approaches don't really work. The difference, again, I apologize for that as Clipped, the difference between no summary and the compaction coming out of open code, for example, is negligible. So you can basically throw away that compaction entirely, and it's only minorly worse than using the sort of built in compaction tool from open code, but if you do a smart compaction with a better prompt, you can be much better.

## Conclusion and Final Thoughts

All right, well thank you very much for listening, I'm Jeff, and Mr. Robin.