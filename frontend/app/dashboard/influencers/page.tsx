"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { useInfluencers } from "@/lib/hooks/use-influencers";
import { useTechnologies } from "@/lib/hooks/use-technologies";
import { formatNumber, getPlatformIcon } from "@/lib/utils";
import { Search, Filter, Grid3X3, List, ChevronLeft, ChevronRight } from "lucide-react";
import Link from "next/link";

export default function InfluencersPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [selectedTech, setSelectedTech] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");

  const { data, isLoading } = useInfluencers({
    page,
    page_size: 12,
    search: search || undefined,
    technology_id: selectedTech || undefined,
  });

  const { data: techData } = useTechnologies();

  const influencers = data?.items || [];
  const totalPages = data?.pages || 1;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold">Influencers</h1>
            <p className="text-muted-foreground mt-1">
              Discover and track AI tech influencers
            </p>
          </div>
          <Button>Add Influencer</Button>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row gap-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search influencers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9"
            />
          </div>
          <div className="flex gap-2">
            <Button variant="outline" size="icon">
              <Filter className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "grid" ? "default" : "outline"}
              size="icon"
              onClick={() => setViewMode("grid")}
            >
              <Grid3X3 className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "outline"}
              size="icon"
              onClick={() => setViewMode("list")}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {/* Technology Filter */}
        <div className="flex flex-wrap gap-2">
          <Badge
            variant={selectedTech === null ? "default" : "secondary"}
            className="cursor-pointer"
            onClick={() => setSelectedTech(null)}
          >
            All
          </Badge>
          {techData?.items?.map((tech: any) => (
            <Badge
              key={tech.id}
              variant={selectedTech === tech.id ? "default" : "secondary"}
              className="cursor-pointer"
              style={
                selectedTech === tech.id && tech.color
                  ? { backgroundColor: tech.color }
                  : {}
              }
              onClick={() =>
                setSelectedTech(selectedTech === tech.id ? null : tech.id)
              }
            >
              {tech.name}
            </Badge>
          ))}
        </div>

        {/* Results */}
        {isLoading ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {[...Array(6)].map((_, i) => (
              <Card key={i} className="animate-pulse">
                <CardContent className="p-6 h-48" />
              </Card>
            ))}
          </div>
        ) : (
          <>
            <div
              className={
                viewMode === "grid"
                  ? "grid gap-4 md:grid-cols-2 lg:grid-cols-3"
                  : "space-y-4"
              }
            >
              {influencers.map((influencer: any) => (
                <Link
                  key={influencer.id}
                  href={`/dashboard/influencers/${influencer.id}`}
                >
                  <Card
                    className={
                      viewMode === "list"
                        ? "hover:bg-accent transition-colors"
                        : "h-full hover:bg-accent transition-colors"
                    }
                  >
                    <CardContent
                      className={
                        viewMode === "list"
                          ? "p-4 flex items-center gap-4"
                          : "p-6"
                      }
                    >
                      <Avatar
                        className={
                          viewMode === "list" ? "h-12 w-12" : "h-16 w-16 mb-4"
                        }
                      >
                        <AvatarImage src={influencer.profile_image_url} />
                        <AvatarFallback>
                          {influencer.full_name.charAt(0)}
                        </AvatarFallback>
                      </Avatar>

                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold truncate">
                          {influencer.full_name}
                        </h3>
                        <p className="text-sm text-muted-foreground line-clamp-1">
                          {influencer.headline}
                        </p>

                        {viewMode === "grid" && (
                          <>
                            <div className="flex items-center gap-4 mt-3 text-sm">
                              <span className="text-muted-foreground">
                                {formatNumber(influencer.total_followers)} followers
                              </span>
                              <span className="text-muted-foreground">
                                {influencer.content_count} posts
                              </span>
                            </div>

                            <div className="flex flex-wrap gap-1 mt-3">
                              {influencer.technologies
                                ?.slice(0, 3)
                                .map((tech: any) => (
                                  <Badge
                                    key={tech.technology_id}
                                    variant="outline"
                                    className="text-xs"
                                  >
                                    {tech.technology?.name}
                                  </Badge>
                                ))}
                            </div>

                            <div className="flex gap-2 mt-4">
                              {influencer.social_accounts
                                ?.slice(0, 4)
                                .map((account: any) => (
                                  <span
                                    key={account.id}
                                    className="text-lg"
                                    title={account.platform}
                                  >
                                    {getPlatformIcon(account.platform)}
                                  </span>
                                ))}
                            </div>
                          </>
                        )}

                        {viewMode === "list" && (
                          <div className="flex items-center gap-4 mt-1 text-sm text-muted-foreground">
                            <span>
                              {formatNumber(influencer.total_followers)} followers
                            </span>
                            <span>•</span>
                            <span>{influencer.region}</span>
                            <span>•</span>
                            <span>{influencer.company}</span>
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>

            {/* Pagination */}
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">
                Showing {influencers.length} of {data?.total} results
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                >
                  <ChevronLeft className="h-4 w-4 mr-1" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                >
                  Next
                  <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </div>
          </>
        )}
      </div>
    </DashboardLayout>
  );
}
