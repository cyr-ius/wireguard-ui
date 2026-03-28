import { ChangeDetectionStrategy, Component, OnInit, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { ApiService, GithubRelease } from '../../core/services/api.service';
import { APP_INFO } from '../../shared/constants/app-info';

@Component({
  selector: 'app-about',
  standalone: true,
  imports: [DatePipe],
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './about.component.html',
  styleUrl: './about.component.css',
})
export class AboutComponent implements OnInit {
  private readonly api = inject(ApiService);

  readonly appVersion = signal(APP_INFO.fallbackVersion);
  readonly repository = APP_INFO.repository;
  readonly repoUrl = `https://github.com/${this.repository}`;
  readonly issueUrl = computed(
    () =>
      `https://github.com/${this.repository}/issues/new?title=${encodeURIComponent('[Bug] ')}&body=${encodeURIComponent(
        `Version: ${this.appVersion()}\n\nDescribe the issue:\n`
      )}`
  );
  readonly apiUrl = '/api';
  readonly apiDocsUrl = '/api/docs';
  readonly apiStatusUrl = '/api/status';

  readonly checkingUpdate = signal(false);
  readonly updateError = signal<string | null>(null);
  readonly latestRelease = signal<GithubRelease | null>(null);
  readonly updateAvailable = signal(false);

  ngOnInit(): void {
    this.api.getAppVersion().subscribe({
      next: (data) => this.appVersion.set(data.version || APP_INFO.fallbackVersion),
      error: () => this.appVersion.set(APP_INFO.fallbackVersion),
    });
    this.checkForUpdate();
  }

  checkForUpdate(): void {
    this.checkingUpdate.set(true);
    this.updateError.set(null);

    this.api.getLatestGithubRelease(this.repository).subscribe({
      next: (release) => {
        this.latestRelease.set(release);
        this.updateAvailable.set(this.isNewerVersion(release.tag_name, this.appVersion()));
        this.checkingUpdate.set(false);
      },
      error: () => {
        this.updateError.set('Unable to check latest release on GitHub.');
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
      .replace(/^v/i, '')
      .split('.')
      .map((part) => Number.parseInt(part.replace(/\D.*/, ''), 10))
      .filter((part) => Number.isFinite(part));
  }
}
