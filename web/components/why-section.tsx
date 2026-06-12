import { InformationCircleIcon } from "@/components/icons";

export function WhySection() {
  return (
    <section
      aria-labelledby="why-section-heading"
      className="mt-5"
    >
      <div className="rounded-lg border border-blue-200 bg-blue-50 px-4 py-3 shadow-sm">
        <div className="flex gap-2.5">
          <InformationCircleIcon className="mt-0.5 size-5 shrink-0 text-blue-700" />
          <div>
            <h2 id="why-section-heading" className="text-base font-semibold text-blue-950">
              Why this matters
            </h2>
            <p className="mt-1 text-sm leading-snug text-blue-900">
              The county plans for mail-in elections. If federal law ends that option for most residents
              (military and overseas voters excepted) and removes ballot machines, voting would move in
              person to Voter Service Polling Centers. The county has not planned for this, so citizens
              are building a backup plan. Use this site to find your assigned center and see voters spread
              evenly across VSPCs, so each location can handle paper ballots cast and counted there on the
              same day.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
