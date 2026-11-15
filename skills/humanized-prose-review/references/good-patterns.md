# Good patterns

This page is a list of 22 habits of clear explanatory and
argumentative writing, each with a short example. The other files in
this folder list tells: words and sentence shapes that make writing
read as if a machine wrote it. When you cut a tell from a draft, write
a sentence that follows one of these habits in its place. In some
sections a weaker version comes first, for comparison.

## 1. Open with your claim and your reason, then give the cost

Write your claim in the first sentence, in plain words, with your
reason for it, so that a reader who stops after that sentence knows
what you think and why. Then say what each choice costs and what could
go wrong, in numbers if you have them.

Weaker:

> This note looks at our backup setup and some options going forward.

Better:

> We should move the nightly backups to a second disk, because the
> current disk fills up on busy nights and the backup job failed on
> three of the last seven. Each time the job fails, about 40 GB of
> customer uploads have no second copy until the next run succeeds. A
> second 4 TB disk costs about $100, and an engineer needs about an
> hour to install it.

## 2. Give the facts before any summary word

Give the numbers and the events before you use a word such as "slow"
or "serious", because readers who see the facts in order can tell for
themselves how serious the event was. When you need to say what went
wrong, give the grounds in the same sentence: write "the script does
not check free disk space before it starts" in place of "the script is
fragile".

Weaker:

> The database migration was a disaster.

Better:

> The migration script started at 02:00 and had copied 60 percent of
> the rows by 02:40. At 03:10 the database server's disk filled up. We
> finished the rollback at 07:30, an hour after our online store's
> 06:30 opening time.

## 3. Follow a general claim with one case, and say what causes what

When you state a general claim, follow it with one case that has
numbers, and say what causes what, so the reader can check the claim
against the case.

> Dissolved salt raises the boiling point of water in proportion to the
> amount of salt in each liter. A tablespoon of table salt, about 18
> grams, in four liters of pasta water raises the boiling point by less
> than a tenth of a degree Celsius, so the salt changes the taste of the
> pasta and barely changes the cooking time.

## 4. Make the actor the subject and put the action in the verb

Make the person or machine that acts the subject of the sentence, and
put the action in a verb. If you write a noun such as "compilation" or
"occurrence", the reader cannot see who does what.

Weaker:

> Compilation of each branch occurs on push.

Better:

> The build server compiles each branch when someone pushes to it.

## 5. Define each term before you use it in an argument

If your readers use a word in different senses, tell them which sense
you mean before you use the word in an argument; otherwise each reader
checks your argument against their own sense of the word. For a term
the reader may not know, say in one plain sentence what the thing
does, as in "a load balancer passes each incoming request to one of
several servers".

> In this report, I count the service as down when more than half of
> its health checks fail for five minutes in a row. The team disagrees
> about whether last Tuesday's slowdown was an outage. During Tuesday's
> twelve minutes of slow responses, fewer than half of the health
> checks failed, so by this definition the service was not down.

## 6. List what everyone agrees on, then argue the question that is left

List the points that no one in the discussion disputes. The questions
still in dispute are then the only ones you need to argue, and you can
write the rest of the document about them.

> Both teams agree that customers must see a new price on the product
> page after staff change it, and both teams accept a delay of up to
> ten seconds. They disagree about one thing: whether customers may see
> the old price for five minutes when staff lower a price during a
> sale.

## 7. State the mistaken belief before you correct it

If you correct a belief, first state the belief in the words of people
who believe it. If you only deny it, the reader has to guess what you
are correcting.

Weaker:

> A higher-wattage charger will not damage your laptop.

Better:

> You may have heard that a charger rated for more watts than your
> laptop needs will overload the laptop. But the laptop draws only the
> power it needs, so a 60-watt laptop on a 100-watt USB-C charger uses
> at most 60 watts.

## 8. Give the reason people choose the other option, then answer that reason

State the other side's reason in the words its supporters would use,
and then answer that reason.

Weaker:

> Retrying a failed request immediately is a mistake.

Better:

> A client should wait a short random delay before it retries a failed
> request. A programmer who makes the client retry at once has a good
> reason: most failures are brief, and the request usually succeeds the
> second time. When the failure was brief, though, the client loses
> only a few hundred milliseconds by waiting. And when the server fails
> because it is overloaded, every client that got an error retries at
> the same moment, and the server receives the same burst of requests
> again. If each client waits a random delay, the retries reach the
> server spread out over time, and the server receives fewer requests
> in any one second.

## 9. Agree that the conclusion would follow from the premise, then show that the premise is false

When someone argues from a premise you think is false, agree that
their conclusion would be right if the premise were true, and then give
the evidence against the premise. The form is: if X were true, Y would
be true, but X is not true. The reader then knows which fact you and
the other side disagree about.

> We will not speed up the slow queries by adding memory to the
> database server. If the server were running out of memory, we could
> make the queries faster by adding more, but at peak load the server
> uses 9 of its 32 GB, and the whole orders table, at 4 GB, already
> fits in memory. The queries are slow because the database reads every
> row of the orders table for each one: the customer ID column has no
> index.

## 10. Test the opposing rule on one case, then give a condition the reader can apply to new cases

Apply the opposing rule to one of its own examples, or to a case you
construct, and say what someone who followed the rule would do. Then
state your own condition in a form the reader can check against a new
case.

> Build time is the wrong test for deciding which pages to cache. Under
> the proposed rule, the server caches any page that takes it more than
> a second to build. The server takes two seconds to build the account
> balance page, so it would cache that page, and a customer who had
> just made a transfer would see the old balance. Cache a page only
> when the information on it stays the same for longer than the server
> keeps the cached copy. By that test, the server should not cache the
> balance page, which shows a new figure after every transfer, and
> should cache the opening-hours page, which staff edit only when the
> store's hours change.

## 11. Before you trust a count, find out how many cases could have been counted

If people use one version of an app in more sessions than another,
that version sends more crash reports even when it crashes no more
often per session. Compare rates, such as crashes per thousand
sessions.

> The app crashes less often on version 5.2 than on 5.1, even though
> most of this week's crash reports came from 5.2. Eighty percent of
> this week's sessions ran on 5.2, so most reports would come from 5.2
> even if the app crashed as often on 5.2 as on 5.1. Per thousand
> sessions, the app crashed 1.1 times on 5.2 and 1.3 times on 5.1.

## 12. Use an example from another field to show that two changes cannot be told apart, then test one change at a time

When two changes happened in the same week, state your case, then
describe the same situation in another field, where the reader has no
reason to favor either change, and say which part of the example
matches which part of your case. Then describe a test that changes one
thing at a time.

> We cannot tell from build times alone why our builds got slower,
> because in the same week we moved to a new continuous integration
> provider and added 400 integration tests. A runner who buys new shoes
> in the same week she switches to a hillier route cannot tell from her
> times whether the shoes or the hills slowed her down. Our new
> provider corresponds to her shoes, and our new tests to the hills. To
> measure the provider alone, we can build last month's commit, which
> has none of the new tests, on both providers and compare the times.

## 13. Say how many cases you checked, how many showed the result, and where you did not look

A reader cannot weigh "I found it in six repositories" without the
total you searched, and cannot see the limits of your search unless you
name what you left out.

> Six of our 212 repositories import the old logging library; I
> searched all 212. I did not search scripts that people keep outside
> version control, so some of those scripts may import the library too.

## 14. When you compare two things, say which part matches which

When you use an analogy, say which part of the familiar thing matches
which part of the new one, and choose a familiar thing whose parts
relate to each other the way the new thing's parts do. Use a metaphor
only when you can say which part of it matches which part of the
mechanism; otherwise describe the mechanism in plain words, as in the
second example.

> A database index works like the index at the back of a cookbook. At
> the back of a cookbook, each ingredient is listed with the numbers of
> the pages it appears on. In a database index, each value in a column
> is stored with the locations of the rows where it appears. With
> either one, you can find every match without reading every page or
> every row.

> The packing station packs fewer orders per hour than any other
> station, and every order passes through it, so if we speed up any
> other station, we still ship the same number of orders per hour.

## 15. Hedge only where you are unsure, and say how you would find out

If you hedge everything, the reader cannot tell your real doubts from
habit, so give each hedge a size or a reason ("roughly 50 MB",
"probably, because …"), and name the test you will run.

> The app's memory use grows by roughly 50 MB an hour. The image cache
> is probably the cause: when I turned the cache off, memory use
> stopped growing, but with the cache off the app also reloads every
> image from disk, so I changed more than one thing in that test. After
> an hour of use I will take a heap dump, a snapshot of everything in
> the app's memory, and check whether cached images take up all of the
> extra 50 MB.

## 16. When you quote a source, say what the quotation means for the reader's case

When you quote documentation or another source, tell the reader what
the quotation means for their situation, in their terms.

> If your pump runs eight hours a day, service the valve about every
> two months. The manual says the valve "must be serviced at intervals
> not exceeding 500 hours", and 500 hours at eight hours a day is about
> 62 days.

## 17. Write a parallel pair or a list of three only when each item is a separate fact

If you put an item in a list only for the rhythm, the reader spends
time looking for the fact in it, so cut that item.

Weaker:

> The new router is faster, simpler and smarter.

Better:

> The new router is three times as fast (900 megabits per second
> against 300), has one settings page in place of four, and moves each
> device to whichever Wi-Fi band is less busy.

You can also teach a distinction with a parallel pair, followed by one
case that applies it.

> Baking soda needs an acid in the batter, such as buttermilk or
> yogurt, to produce carbon dioxide. Baking powder already contains an
> acid, so a batter made with plain milk needs baking powder.

## 18. Number a short sequence inside the sentence, and put a long procedure in a numbered list

Number two or three steps inside the sentence. If a procedure is long
enough that the reader will check off each step, write it as a
numbered list.

> To reset the pump, first, turn it off at the switch; second, wait ten
> seconds; third, turn it on again.

> To replace the filter cartridge:
>
> 1. Turn off the pump.
> 2. Open the pressure-release valve on the filter housing, and wait
>    until no more water comes out.
> 3. Unscrew the housing.
> 4. Lift out the old cartridge.
> 5. Push the new cartridge into place.
> 6. Tighten the housing by hand.

## 19. Say how each sentence follows from the one before

Use words such as "so", "because" and "but" to say how each sentence
or clause relates to the one before it, so the reader does not have to
guess whether you are giving a cause, a result or an exception.

> The train is due at 14:10, the last ferry leaves at 14:30, and the
> walk from the station to the pier takes ten minutes, so if your train
> is more than ten minutes late, you will miss the ferry.

## 20. Write long sentences for a series of attempts, and short ones for a single fact

Use a long sentence for a series of attempts or a chain of causes, and
a short sentence for a single fact the reader needs to remember.

> The import job failed because row 48,112 has a date in the year
> 20024. Before we found that row, we raised the memory limit, split
> the job in two and moved it to a larger machine, and each time the
> job ran for about an hour and stopped with the same error.

## 21. Write in the first person when your own observation is the evidence

A reader can weigh what you saw only if they know you saw it, so say
"I saw", and say when and what.

> Last March I watched the clock-drift alarm stay silent while the
> clocks on both of our database machines were four seconds fast. Both
> machines set their clocks from the same time server, and that server
> was itself four seconds fast. The alarm compared the two machines'
> clocks with each other and fired only when they differed, so it never
> fired.

## 22. End a section with a test the reader can apply, or return to the case you opened with

A reader who finishes a section should be able to act on it, so close
with a test they can apply or with the general point applied to your
opening case.

> Count the migration as finished when every service reads from the new
> database, no service has written to the old database for seven days,
> and you have restored a backup taken from the new database to a spare
> server and checked the restored data against the live database.
