"use client";

import { useParams } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  useInfluencer,
  useInfluencerContent,
  useSimilarInfluencers,
} from "@/lib/hooks/use-influencers";
import { formatNumber, formatDate, getPlatformIcon } from "@/lib/utils";
import {
  MapPin,
  Building2,
  Link as LinkIcon,
  Mail,
  Bookmark,
  ExternalLink,
} from "lucide-react";
import Link from "next/link";

export default function InfluencerDetailPage() {
  const params = useParams();
  const id = params.id as string;

  const { data: influencer, isLoading } = useInfluencer(id);
  const { data: contentData } = useInfluencerContent(id, { page_size: 6 });
  const { data: similarData } = useSimilarInfluencers(id);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="animate-pulse space-y-6">
          <div className="h-48 bg-card rounded-lg" />
          <div className="grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2 h-96 bg-card rounded-lg" />
            <div className="h-96 bg-card rounded-lg" />
          </div>
        </div>
      </DashboardLayout>
    );
  }

  if (!influencer) {
    return (
      <DashboardLayout>
        <div className="flex flex-col items-center justify-center py-20">
          <h1 className="text-2xl font-bold">Influencer not found</h1>
          <p className="text-muted-foreground mt-2">
            The influencer you&apos;re looking for doesn&apos;t exist.
          </p>
          <Link href="/dashboard/influencers">
            <Button className="mt-4">Back to Influencers</Button>
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Profile Header */}
        <Card>
          <CardContent className="p-6">
            <div className="flex flex-col md:flex-row gap-6">
              <Avatar className="h-24 w-24">
                <AvatarImage src={influencer.profile_image_url} />
                <AvatarFallback className="text-3xl">
                  {influencer.full_name.charAt(0)}
                </AvatarFallback>
              </Avatar>

              <div className="flex-1 min-w-0">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                  <div>
                    <h1 className="text-2xl font-bold">
                      {influencer.full_name}
                    </h1>
                    <p className="text-muted-foreground mt-1">
                      {influencer.headline}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm">
                      <Bookmark className="h-4 w-4 mr-2" />
                      Watchlist
                    </Button>
                    <Button size="sm">Follow Up</Button>
                  </div>
                </div>

                <div className="flex flex-wrap gap-4 mt-4 text-sm text-muted-foreground">
                  {influencer.company && (
                    <div className="flex items-center gap-1">
                      <Building2 className="h-4 w-4" />
                      {influencer.company}
                    </div>
                  )}
                  {influencer.city && influencer.country_code && (
                    <div className="flex items-center gap-1">
                      <MapPin className="h-4 w-4" />
                      {influencer.city}, {influencer.country_code}
                    </div>
                  )}
                  {influencer.website_url && (
                    <Link
                      href={influencer.website_url}
                      target="_blank"
                      className="flex items-center gap-1 hover:text-primary"
                    >
                      <LinkIcon className="h-4 w-4" />
                      Website
                    </Link>
                  )}
                  {influencer.email_public && (
                    <div className="flex items-center gap-1">
                      <Mail className="h-4 w-4" />
                      {influencer.email_public}
                    </div>
                  )}
                </div>

                <div className="flex flex-wrap gap-2 mt-4">
                  <Badge variant="secondary">
                    {formatNumber(influencer.total_followers)} followers
                  </Badge>
                  <Badge variant="secondary">
                    {influencer.content_count} posts
                  </Badge>
                  {influencer.overall_rank && (
                    <Badge variant="default">
                      Rank #{influencer.overall_rank}
                    </Badge>
                  )}
                  {influencer.technologies?.map((tech: any) => (
                    <Badge key={tech.technology_id} variant="outline">
                      {tech.technology?.name}
                    </Badge>
                  ))}
                </div>

                {/* Social Links */}
                <div className="flex gap-3 mt-4">
                  {influencer.social_accounts?.map((account: any) => (
                    <Link
                      key={account.id}
                      href={account.url}
                      target="_blank"
                      className="flex items-center gap-2 px-3 py-1.5 rounded-md bg-accent hover:bg-accent/80 transition-colors"
                    >
                      <span className="text-lg">
                        {getPlatformIcon(account.platform)}
                      </span>
                      <span className="text-sm font-medium">
                        {formatNumber(account.followers_count || 0)}
                      </span>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Content Section */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Content</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {contentData?.items?.map((content: any) => (
                <div
                  key={content.id}
                  className="flex gap-4 p-4 rounded-lg border"
                >
                  {content.thumbnail_url && (
                    <img
                      src={content.thumbnail_url}
                      alt={content.title}
                      className="w-32 h-20 object-cover rounded-md"
                    />
                  )}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">
                        {getPlatformIcon(content.platform)}
                      </span>
                      <span className="text-sm text-muted-foreground capitalize">
                        {content.content_type}
                      </span>
                    </div>
                    <h3 className="font-semibold mt-1 line-clamp-2">
                      {content.title}
                    </h3>
                    <p className="text-sm text-muted-foreground mt-1">
                      {formatDate(content.published_at)}
                    </p>
                  </div>
                  <Link
                    href={content.original_url}
                    target="_blank"
                    className="self-center"
                  >
                    <Button variant="ghost" size="icon">
                      <ExternalLink className="h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Similar Influencers */}
        <Card>
          <CardHeader>
            <CardTitle>Similar Influencers</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {similarData?.map((inf: any) => (
                <Link
                  key={inf.id}
                  href={`/dashboard/influencers/${inf.id}`}
                >
                  <div className="flex items-center gap-4 p-4 rounded-lg border hover:bg-accent transition-colors">
                    <Avatar>
                      <AvatarImage src={inf.profile_image_url} />
                      <AvatarFallback>{inf.full_name.charAt(0)}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium truncate">{inf.full_name}</h3>
                      <p className="text-sm text-muted-foreground">
                        {formatNumber(inf.total_followers)} followers
                      </p>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
}
