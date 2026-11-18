---
name: Owner brief and answers
description: The owner's original brief for the project and every answer and change of direction given on 2026-11-13, kept verbatim as raw source material
type: source
date: 2026-11-13
author: owner
tags:
  - type/source
  - project/kanon
aliases:
  - Original brief
  - Owner brief
---

# Owner brief and answers (2026-11-13)

Raw source, kept as written. Working documents do not read this file directly; they read
the decision records compiled from it (Koine discipline 9, sources inbox). Compiled into:
[docs/decisions/](../decisions/INDEX.md) and the
[foundation plan](../../plans/2026-11-13-kanon-foundation/plan.md).

## 1. Original brief

> this is a new repo to create a project similar to a proposed idea for an autonomous AI creation machine, first dubbed "agora". this is to supercede it, hence the Latin name "Mercatus". The overarching idea is to create an engine that allows users to keep a layer of context across an entire project, so that different specialist roles can contribute to a shared repo with context and documentation about features, builds, fixes, ideas, etc and a "marketplace" of specialised agents will use that context to build out the desired product.
> This engine needs to exist initially as a blank slate. a module that can be easily imported into any repo and begin working immediately through whatever AI model is connected to it. it should expand alongside the user's requirements and alongside the project itself to be everything they need it to be, and to help create whatever it is they lay out their requirements for.
> As a basis, three agent harnesses were created by Github user Antikas called "Pinax", "Autobuild" and "Ergasterion". These would exist as part of the marketplace and be called upon by the engine as it required them. I want to expand this idea so that the engine has access to a wide variety of agents, each specialised to a specific skill within an ecosystem and these models are added in as they are required, as if onboarding a new expert in a team.
> This engine should follow the Koine loop, as defined in Antikas' "koine-os" project in which an independent subagent reviewer reviews all agent output to refine it before passing back to a human user for explicit approval. Documentation should be heart of this context engine, keeping human-facing and readable documentation alongside everything created so that the specialist teams using this are always in the loop and up-to-date about whats happening in it.
> Research the projects I've given you and report back to me with a detailed plan on how this idea is achievable. Ask questions as required, do your own research, make sure all decisions have backing and don't infer information that doesn't have extensive support.

## 2. Answers to the seven questions in plan revision 1

> 1. agora was an idea, not a repo. i can't provide more information on it, its just background.
> 2. everything should be in scope. this engine should work to take and refine the users requirements into actionable steps, create work tickets to carry them out, call on the required tools (such as ergasterion) to turn those work tickets into actual code. one might create a poc, one might oversee security, one could create code automations, etc.
> 3. the engine should pull these in as needed. it would need an actual central marketplace to hold the agents and an easy way for new ones to be submitted and for existing engines to pull them in as required.
> 4. there should be human approval on major gates, where plans/decisions/documentation/etc are given to the user clearly and they approve or request changes where they see fit.
> 5. for now, claude code. but this should work theoretically with whatever assistant accesses the project.
> 6. these are suitable
> 7. not yet, I want to prove it in myself first and come to a project once the core is functional

## 3. Naming

> mercatus is the latin name for a marketplace already. my naming convention need-be reevaluated. i want to stick with koine's greek naming convention. if the marketplace is a collection of agents and tools named after mythology, it should have a suitable name for it. then the engine itself need have a better name too.

Chosen in a question: marketplace **Pantheon**. Engine name requirements, as given across
the following answers:

> whilst being true to the naming convention, this also need have a memorable and easily-spellable name so that people are able to use it. reevaluate.

> I've changed my mind. Athena is a far more fitting name for this engine, as it manages the wisdom and strategy of the team using it. check whether this would be an issue

> I want something shorter than Parthenon, preferably 6 letters max, and easy to spell and pronounce phonetically, that's close enough in the projects meaning to the character's purpose

> suggest further options, exploring more into the project itself's purpose rather than just athenas role. perhaps explore into options similar to koine in being a common ancient greek word rather than a mythological character

Chosen in a question: engine **Kanon**.

## 4. GitHub and cost

> to make the engine clearer in how it works and have some mechanical grounding to lean on, i would like to give it a start via using github. this should be an optional addition to make it work better for users or larger groups. I want it to make full use of github projects for tracking the work tickets created and where tools are in their production, tie this to branches which can be merged together into reviewable PRs that have a breakdown in the description, and the reviewer notes underneath. this can better keep track of work and history in a human-readable way as well as within the repo itself for the agents. this should keep in mind action minutes for small groups, and not use them unnecessarily. the entire loop should be token-conscious as well and not burn through money for very little output.

## 5. Start of Phase 0

> begin phase 0.
