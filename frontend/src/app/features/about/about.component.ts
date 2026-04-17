import { DatePipe } from "@angular/common";
import { ChangeDetectionStrategy, Component, OnInit, computed, effect, inject, signal } from "@angular/core";
import { ErrorField } from "../../core/applets/error-field.component";
import { ApiError } from "../../core/models/api-error.model";
import { ApiService, GithubRelease } from "../../core/services/api.service";

@Component({
  selector: "app-about",
  standalone: true,
  imports: [DatePipe, ErrorField],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: "./about.component.html",
  styleUrl: "./about.component.css",
})
export class AboutComponent implements OnInit {
  private readonly api = inject(ApiService);

  readonly appVersion = signal("Development");
  readonly repository = signal("");
  readonly repoUrl = computed(() => `https://github.com/${this.repository()}`);
  readonly issueUrl = computed(
    () =>
      `https://github.com/${this.repository()}/issues/new?title=${encodeURIComponent("[Bug] ")}&body=${encodeURIComponent(
        `Version: ${this.appVersion()}\n\nDescribe the issue:\n`,
      )}`,
  );
  readonly apiUrl = "/api";
  readonly apiDocsUrl = "/api/docs";
  readonly apiStatusUrl = "/api/health";

  readonly checkingUpdate = signal(false);
  readonly error = signal<ApiError | null>(null);
  readonly latestRelease = signal<GithubRelease | null>(null);
  readonly updateAvailable = signal(false);

  constructor() {
    effect(() => {
      if (this.repoUrl()) this.checkForUpdate();
    });
  }

  ngOnInit(): void {
    this.api.getAppVersion().subscribe({
      next: (data) => {
        this.appVersion.set(data.version || "Development");
        this.repository.set(data.repository);
      },
      error: () => this.appVersion.set("Development"),
    });
  }

  checkForUpdate(): void {
    this.checkingUpdate.set(true);
    this.error.set(null);

    this.api.getLatestGithubRelease(this.repository()).subscribe({
      next: (release) => {
        this.latestRelease.set(release);
        this.updateAvailable.set(this.isNewerVersion(release.tag_name, this.appVersion()));
        this.checkingUpdate.set(false);
      },
      error: () => {
        this.error.set({ code: "about", message: "Unable to check latest release on GitHub." } as ApiError);
        this.checkingUpdate.set(false);
      },
    });
  }

  private isNewerVersion(remote: string, local: string): boolean {
    const r = this.normalizeVersion(remote);
    const l = this.normalizeVersion(local);
    const maxLength = Math.max(r.length, l.length);

    for (let i = 0; i < maxLength; i += 1) {
      const rv = r[i] ?? 0;
      const lv = l[i] ?? 0;
      if (rv > lv) return true;
      if (rv < lv) return false;
    }

    return false;
  }

  private normalizeVersion(version: string): number[] {
    return version
      .replace(/^v/i, "")
      .split(".")
      .map((part) => Number.parseInt(part.replace(/\D.*/, ""), 10))
      .filter((part) => Number.isFinite(part));
  }
}
