
locals {
  postgres_db_name = "eff"
  postgres_username = "eff_user"
}

resource "aws_db_subnet_group" "db_subnet_group_for_postgres_db" {
  name       = lower("${var.service_name}__${var.environment}__DB_Subnet_Group")
  subnet_ids = [aws_subnet.vpc_main__public_subnet_az1.id, aws_subnet.vpc_main__public_subnet_az2.id]
}

resource "aws_db_instance" "postgres_database" {
  identifier = lower("${var.service_name_hyphens}-${var.environment_hyphens}-Postgres-Database")

  // Engine
  engine = "postgres"
  engine_version = "15"

  // Sizing
  instance_class = "db.t4g.micro"
  multi_az = false
  storage_type = "gp3"
  allocated_storage = 20
  max_allocated_storage = 100

  // Connection & security details
  db_name = local.postgres_db_name
  port = 5432
  username = local.postgres_username
  password = var.POSTGRES_PASSWORD
  storage_encrypted = true

  // Networking
  db_subnet_group_name = aws_db_subnet_group.db_subnet_group_for_postgres_db.name
  vpc_security_group_ids = [aws_security_group.security_group_database.id]
  publicly_accessible = false

  // Upgrades
  auto_minor_version_upgrade = true
  allow_major_version_upgrade = false
  maintenance_window = "Mon:04:00-Mon:05:00"

  // Backups and deletion
  deletion_protection = true
  backup_retention_period = 35
  backup_window = "02:00-03:00"
  copy_tags_to_snapshot = true
  delete_automated_backups = false
  skip_final_snapshot = false
  final_snapshot_identifier = "${var.service_name_hyphens}-${var.environment_hyphens}-Postgres-Database-Final-Snapshot"

  // Logging & monitoring
  enabled_cloudwatch_logs_exports = ["postgresql"]
  monitoring_role_arn = aws_iam_role.rds_enhanced_monitoring.arn
  monitoring_interval = 60
}

resource "aws_iam_role" "rds_enhanced_monitoring" {
  name_prefix        = "rds-enhanced-monitoring-"
  assume_role_policy = data.aws_iam_policy_document.rds_enhanced_monitoring.json
}

resource "aws_iam_role_policy_attachment" "rds_enhanced_monitoring" {
  role       = aws_iam_role.rds_enhanced_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

data "aws_iam_policy_document" "rds_enhanced_monitoring" {
  statement {
    actions = [
      "sts:AssumeRole",
    ]

    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["monitoring.rds.amazonaws.com"]
    }
  }
}