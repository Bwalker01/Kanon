---
type: sources
status: reference
updated: 2026-11-16
---

# Owner Sources

> **Summary:** The owner's requests and answers, recorded verbatim. Decisions in
> `kanon/decisions/` are derived from these; agents work from the decisions, not from this file.

## 1. Original Brief (2026-11-13)
> this is a new repo to create a project similar to a proposed idea for an autonomous AI creation machine, first dubbed "agora". this is to supercede it, hence the Latin name "Mercatus". The overarching idea is to create an engine that allows users to keep a layer of context across an entire project, so that different specialist roles can contribute to a shared repo with context and documentation about features, builds, fixes, ideas, etc and a "marketplace" of specialised agents will use that context to build out the desired product.
> This engine needs to exist initially as a blank slate. a module that can be easily imported into any repo and begin working immediately through whatever AI model is connected to it. it should expand alongside the user's requirements and alongside the project itself to be everything they need it to be, and to help create whatever it is they lay out their requirements for.
> As a basis, three agent harnesses were created by Github user Antikas called "Pinax", "Autobuild" and "Ergasterion". These would exist as part of the marketplace and be called upon by the engine as it required them. I want to expand this idea so that the engine has access to a wide variety of agents, each specialised to a specific skill within an ecosystem and these models are added in as they are required, as if onboarding a new expert in a team.
> This engine should follow the Koine loop, as defined in Antikas' "koine-os" project in which an independent subagent reviewer reviews all agent output to refine it before passing back to a human user for explicit approval. Documentation should be heart of this context engine, keeping human-facing and readable documentation alongside everything created so that the specialist teams using this are always in the loop and up-to-date about whats happening in it.
> Research the projects I've given you and report back to me with a detailed plan on how this idea is achievable. Ask questions as required, do your own research, make sure all decisions have backing and don't infer information that doesn't have extensive support.

## 2. Answers to Plan Questions (2026-11-13)

> 1. agora was an idea, not a repo. i can't provide more information on it, its just background.
> 2. everything should be in scope. this engine should work to take and refine the users requirements into actionable steps, create work tickets to carry them out, call on the required tools (such as ergasterion) to turn those work tickets into actual code. one might create a poc, one might oversee security, one could create code automations, etc.
> 3. the engine should pull these in as needed. it would need an actual central marketplace to hold the agents and an easy way for new ones to be submitted and for existing engines to pull them in as required.
> 4. there should be human approval on major gates, where plans/decisions/documentation/etc are given to the user clearly and they approve or request changes where they see fit.
> 5. for now, claude code. but this should work theoretically with whatever assistant accesses the project.
> 6. these are suitable
> 7. not yet, I want to prove it in myself first and come to a project once the core is functional

## 3. Naming (2026-11-13 to 2026-11-15)

> mercatus is the latin name for a marketplace already. my naming convention need-be reevaluated. i want to stick with koine's greek naming convention. if the marketplace is a collection of agents and tools named after mythology, it should have a suitable name for it. then the engine itself need have a better name too.

Chosen in a question: marketplace **Pantheon**. Engine name requirements, as given across
the following answers:

> whilst being true to the naming convention, this also need have a memorable and easily-spellable name so that people are able to use it. reevaluate.

> I've changed my mind. Athena is a far more fitting name for this engine, as it manages the wisdom and strategy of the team using it. check whether this would be an issue

> I want something shorter than Parthenon, preferably 6 letters max, and easy to spell and pronounce phonetically, that's close enough in the projects meaning to the character's purpose

> suggest further options, exploring more into the project itself's purpose rather than just athenas role. perhaps explore into options similar to koine in being a common ancient greek word rather than a mythological character

Chosen in a question: engine **Kanon**.

## 4. GitHub and Cost (2026-11-13)

> to make the engine clearer in how it works and have some mechanical grounding to lean on, i would like to give it a start via using github. this should be an optional addition to make it work better for users or larger groups. I want it to make full use of github projects for tracking the work tickets created and where tools are in their production, tie this to branches which can be merged together into reviewable PRs that have a breakdown in the description, and the reviewer notes underneath. this can better keep track of work and history in a human-readable way as well as within the repo itself for the agents. this should keep in mind action minutes for small groups, and not use them unnecessarily. the entire loop should be token-conscious as well and not burn through money for very little output.

## 5. Start of Phase 0 (2026-11-13)

> begin phase 0.

## 6. Agent Conduct and Writing (2026-11-14)

> as part of the engine, agents should be required to ask questions regularly when needing extra information, rather than building out the whole gate and asking them at the end, they should push back against bad ideas and not be "yes-men" to everything, they should be realistic in expectations and act like a peer giving helpful feedback, including criticism. the agents should also speak in a human-like way and avoid verbose or unnecessary language, remaining professional but friendly within acceptable bounds. in any documentation or writing, AI-isms should be avoided at all costs and they should be written naturally and clearly, varying sentence structure and avoiding the repetitive nature of AI writing. questions and instructions should always be clear. Agents should also adapt themselves to the user's capability, using clear technical language if the user is able to, or avoiding overly-technical terms if they are less technically capable. they should gear themselves to provide help and guidance on the level of the user without being patronising, and avoid confusion. improve your own instructions with these parameters and add them as part of the basis of the engine.

## 7. Simplification (2026-11-16)

> there needs to be an easier way for users to interact using this engine, rather than summarising everything in this chat and wading through several lengthy documents, plans and gates. the koine way of doing all of it - including file structure, methods and documentation - will quickly become slow and cumbersome in larger projects and is already making it difficult to navigate and answer questions. there needs to be clearer identification to folders and to what needs reviewing. the amount of files produced can be optimised and the information in the files is far too wordy and overly complicated. Produced files should also have a more professional tone, they read too informal currently. They should be laid out clearly and satisfyingly, with obvious headers and summaries

Chosen in questions: a single `kanon/` folder; one file per piece of work; daily log, per-folder
indexes, tags and aliases dropped; sources kept; Phase 0 restructured before approval.

## 8. Approvals (2026-11-16)

> R-1:
> All 9 decisions approved
> R-2:
> Approved.

## 9. Phase Order (2026-11-17)

> phases 2 and 3 seem out of order. the branches and pull requests should be a basis created earlier, preferably rolled into this current phase 1 building. the github project board wouldn't be viable until after the branches and prs were sorted anyway

Chosen in questions: Kanon's GitHub identity is a GitHub App; the revised order is approved; the
Phase 1 work file's plan-first exception is accepted.

## 10. Agent Files and Profiles (2026-11-17)

> yes do add it. any necessary information for the claude file to run the engine should be imported into it. identify and split out the agent instructions into specific ones for me and the behavioural standard for Kanon itself

> this will need to be sorted for when the project goes ahead too, as each individual user in a repo that's using Kanon will need their own profile. these would all risk overlapping/overwriting when teams push to remote. all agent files will need to be added to gitignore, even when this project is imported in live environments. figure out a way this can be optimised and best done for when this exists in real environments and how that can apply here too.

> R-1 approve

## 11. Owner Actions (2026-11-18)

> give me everything that needs doing on my side, and make sure that its reflected easily and kept up to date in the project in some way to make it easier to do

## 12. Desk and Atlas (2026-11-18)

> owner setup doesn't need to be kept in the repo, instructions for the creation of things relating directly to the setup of this repo can be kept as current actions within the REVIEW file (which could be better named now that it includes actions). for all general repos, REVIEW.md and STATUS.md shouldn't be committed right? maybe status can, but REVIEW again pertains to the current local user's actions and decisions so these may be useful on the current branch if people switch between them but in the core project, where multiple features are being done at once, these will end up overlapping. consider this and identify a fix.

> could Atlas be an agent archetype extension to koine's existing ones that manages the review and actions required by the user, managing the DESK.md file that gives these steps in an ordered, structured, and easily interactable file? it may require the DESK being expanded out into something more than an md file so that reviews can be more interactive, and actions can be more visually helpful

Chosen in questions: roadmap committed, status generated; the Desk as a self-contained page with no server.

> R-1 approved. actions all complete

The owner also reported the A-5 test session: the setup script is safe and valid, but that session had no Kanon checkout, so the real install was not proven; `uv` may not be on the PATH before the script adds `~/.local/bin`.

## 13. Commit Signing (2026-11-18)

> identify the cause of the commit signing error and ensure it doesn't happen again

Chosen in a question before this: commit unsigned until the signing helper returns.

## 14. Desk Layout (2026-11-18)

> the copy button doesn't work in the desk.html file. its also not very clearly laid out or easy to skim and read. make it generate more interactively (headers as clear tabs, proper buttons, items split into cards that can be expanded for more info

> approve destructive-command-guard

## 15. Review and Action Records (2026-11-19)

> is there a way that the desk can become more integrated with either vscode, claude code or another application as an actual interactive reviewing method, and action step record that you can access without it taking too many excess tokens to recreate every time? it would preferably allow you to see steps ticked with any necessary notes users give about them, and allow users to add review notes to specific files or even directly to any line(s). I'm aiming to make it as easy as possible for any user to explore and use but it also shouldn't take too much away from time or cost of the project that Kanon is doing.

> I like A, I think it would be a good starting point, but it does tie Kanon heavily to github. this may also run into problems on github enterprise where users may not have very elevated permissions with use of Kanon, or the enterprise limits use of projects  or other github features altogether

> does a new agent role need to be added for repository interaction management and tracking or will that be done via communication between Atlas and the scribe one?

Chosen in questions: option A with capability tiers and a Git-only floor; no new role. Plan as P1-11: "yes".

> the github integration review work can be done in the same phase as the github projects integration work, as it won't be necessary until then anyway

## 16. Role Packaging and Roster (2026-11-19)

> can the existing roles be split into their own agents, as expansions that are added via the pantheon as required later? and can the roster of roles be expanded into other possibilities to improve the variety in what Kanon can facilitate?

> this seems okay as is and will be looked into closer to phase 4

## 17. Approvals (2026-11-19)

> approve agent-files-and-profiles
> approve desk-and-atlas
> approve destructive-command-guard

## 18. Remote Session Limits (2026-11-23)

> branch has been merged. that local setup is continuing to work on further local fixes. in the meantime, can you investigate the reasons behind not being able to properly complete tasks in remote sessions and find fixes yourself to manage this problem or suggest to me fixes and ways in which those problems can be circumvented.
