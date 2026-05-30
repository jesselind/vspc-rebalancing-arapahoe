import { ArrowTopRightOnSquareIcon, MapIcon } from "@/components/icons";
import { ButtonLink, PageSection } from "@/components/ui/button";
import { MAP_PDF_URL } from "@/lib/map-pdf-url";

export function PdfViewer() {
  return (
    <PageSection title="County map (PDF)" icon={<MapIcon className="size-6 text-blue-700" />}>
      <p className="text-sm text-zinc-600">
        The full county map opens in a new tab as a PDF from the project repository.
      </p>
      <div className="mt-4">
        <ButtonLink href={MAP_PDF_URL} target="_blank" rel="noopener noreferrer" variant="secondary">
          <ArrowTopRightOnSquareIcon className="size-4" />
          Open county map (PDF)
        </ButtonLink>
      </div>
    </PageSection>
  );
}
