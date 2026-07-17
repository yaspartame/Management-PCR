-- MySQL dump 10.13  Distrib 8.4.10, for Linux (x86_64)
--
-- Host: 144.21.57.156    Database: ipcr_db
-- ------------------------------------------------------
-- Server version	8.0.46

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `tbl_academic_terms`
--

DROP TABLE IF EXISTS `tbl_academic_terms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_academic_terms` (
  `term_id` int NOT NULL AUTO_INCREMENT,
  `academic_year` varchar(20) NOT NULL,
  `semester` varchar(20) NOT NULL,
  `deadline_date` date DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '0',
  PRIMARY KEY (`term_id`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_academic_terms`
--

LOCK TABLES `tbl_academic_terms` WRITE;
/*!40000 ALTER TABLE `tbl_academic_terms` DISABLE KEYS */;
INSERT INTO `tbl_academic_terms` VALUES (1,'2025-2026','1st Semester','2026-07-30',0),(2,'2026-2027','1st Semester','2027-06-30',0),(3,'2026-2027','2nd Semester','2027-12-30',0),(4,'2027-2028','1st Semester','2028-12-15',0),(5,'2027-2028','2nd Semester','2028-01-30',0),(6,'2028-2029','1st Semester','2028-12-22',0),(7,'2029-2030','1st Semester','2029-12-17',0),(8,'2029-2030','2nd Semester','2030-06-30',1);
/*!40000 ALTER TABLE `tbl_academic_terms` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_addselect_targets`
--

DROP TABLE IF EXISTS `tbl_addselect_targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_addselect_targets` (
  `selection_id` int NOT NULL AUTO_INCREMENT,
  `emp_id` int NOT NULL,
  `indicator_id` int NOT NULL,
  `target_source` varchar(50) NOT NULL COMMENT 'e.g., Research Menu, Designation',
  PRIMARY KEY (`selection_id`),
  KEY `fk_addselect_emp` (`emp_id`),
  KEY `fk_addselect_ind` (`indicator_id`),
  CONSTRAINT `fk_addselect_emp` FOREIGN KEY (`emp_id`) REFERENCES `tbl_employee_profiles` (`emp_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_addselect_ind` FOREIGN KEY (`indicator_id`) REFERENCES `tbl_master_indicators` (`indicator_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_addselect_targets`
--

LOCK TABLES `tbl_addselect_targets` WRITE;
/*!40000 ALTER TABLE `tbl_addselect_targets` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_addselect_targets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_audit_logs`
--

DROP TABLE IF EXISTS `tbl_audit_logs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_audit_logs` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `log_timestamp` datetime DEFAULT CURRENT_TIMESTAMP,
  `actor_id` varchar(50) DEFAULT NULL,
  `action_type` varchar(100) NOT NULL,
  `action_details` text NOT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`log_id`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_audit_logs`
--

LOCK TABLES `tbl_audit_logs` WRITE;
/*!40000 ALTER TABLE `tbl_audit_logs` DISABLE KEYS */;
INSERT INTO `tbl_audit_logs` VALUES (1,'2026-04-03 12:26:07','3','Emergency Password Reset','Password reset to default for emp_id: 4','127.0.0.1'),(2,'2026-04-03 12:44:41','3','Emergency Password Reset','Temporary password issued for emp_id: 4','127.0.0.1'),(3,'2026-04-03 15:13:18','3','Emergency Password Reset','Temporary password issued for emp_id: 4','127.0.0.1'),(4,'2026-04-04 00:51:27','3','Emergency Password Reset','Temporary password issued for emp_id: 4','127.0.0.1'),(5,'2026-04-04 01:01:41','3','CSV Roster Import','Import complete: 5 added, 1 updated, 0 unchanged.','127.0.0.1'),(6,'2026-04-07 07:36:27','3','CSV Roster Import','Import complete: 5 added, 1 updated, 0 unchanged.','127.0.0.1'),(7,'2026-04-14 03:09:50','3','CSV Roster Import','Import complete: 4 added, 1 updated, 1 unchanged.','127.0.0.1'),(8,'2026-05-11 15:54:00','3','Term Opened','New term opened: 2027-2028 1st Semester (Deadline: 2028-12-15)','127.0.0.1'),(9,'2026-05-13 02:37:25','3','Term Opened','New term opened: 2027-2028 2nd Semester (Deadline: 2028-01-30)','127.0.0.1'),(10,'2026-06-10 01:30:46','3','Term Opened','New term opened: 2028-2029 1st Semester (Deadline: 2028-12-22)','127.0.0.1'),(11,'2026-06-17 07:33:33','3','Term Opened','New term opened: 2029-2030 1st Semester (Deadline: 2029-12-17)','127.0.0.1'),(12,'2026-06-23 17:47:58','3','Emergency Password Reset','Temporary password issued for emp_id: 4','127.0.0.1'),(13,'2026-06-23 20:13:48','3','Emergency Password Reset','Temporary password issued for emp_id: 51','127.0.0.1'),(14,'2026-06-24 09:23:50','3','Emergency Password Reset','Temporary password issued for emp_id: 53','127.0.0.1'),(15,'2026-06-24 10:50:43','3','Emergency Password Reset','Temporary password issued for emp_id: 49','127.0.0.1'),(16,'2026-06-24 11:14:30','3','Emergency Password Reset','Temporary password issued for emp_id: 81','127.0.0.1'),(17,'2026-06-24 11:21:24','3','Emergency Password Reset','Temporary password issued for emp_id: 52','127.0.0.1'),(18,'2026-06-25 11:58:49','3','Emergency Password Reset','Temporary password issued for emp_id: 49','127.0.0.1'),(19,'2026-06-25 12:00:56','3','Emergency Password Reset','Temporary password issued for emp_id: 53','127.0.0.1'),(20,'2026-06-25 13:24:59','4','DEAN_REVIEW_REJECTED','Dean 4 rejected draft IPCR (review #1). Remarks: EHH','127.0.0.1'),(21,'2026-06-25 13:56:21','4','DEAN_REVIEW_REJECTED','Dean 4 rejected draft IPCR (review #2). Remarks: Ayaw ko pangit','127.0.0.1'),(22,'2026-06-25 13:59:03','4','DEAN_REVIEW_REJECTED','Dean 4 rejected draft IPCR (review #3). Remarks: Missing','127.0.0.1'),(23,'2026-06-25 14:09:15','3','Emergency Password Reset','Temporary password issued for emp_id: 46','127.0.0.1'),(24,'2026-06-25 14:09:57','4','DEAN_REVIEW_APPROVED','Dean 4 approved draft IPCR (review #4). Remarks: Test','127.0.0.1'),(25,'2026-06-25 14:09:58','4','DEAN_REVIEW_REJECTED','Dean 4 rejected draft IPCR (review #4). Remarks: Test','127.0.0.1'),(26,'2026-06-25 14:19:41','4','DEAN_REVIEW_REJECTED','Dean 4 rejected draft IPCR (review #5). Remarks: Test','127.0.0.1'),(27,'2026-06-25 14:26:26','4','DEAN_REVIEW_REJECTED','Dean 4 rejected draft IPCR (review #6). Remarks: Ts is ass','127.0.0.1'),(28,'2026-06-25 15:40:42','3','Emergency Password Reset','Temporary password issued for emp_id: 52','127.0.0.1'),(29,'2026-06-28 05:01:54','3','Term Opened','New term opened: 2029-2030 2nd Semester (Deadline: 2030-06-30)','127.0.0.1'),(30,'2026-06-28 06:16:26','4','DEAN_REVIEW_REJECTED','Dean 4 rejected draft IPCR (review #7). Remarks: sample returm','127.0.0.1');
/*!40000 ALTER TABLE `tbl_audit_logs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_auth_credentials`
--

DROP TABLE IF EXISTS `tbl_auth_credentials`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_auth_credentials` (
  `emp_id` int NOT NULL,
  `corporate_email` varchar(150) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `last_login` datetime DEFAULT NULL,
  `verification_status` enum('PENDING','APPROVED','REJECTED') DEFAULT 'PENDING',
  PRIMARY KEY (`emp_id`),
  UNIQUE KEY `corporate_email` (`corporate_email`),
  CONSTRAINT `fk_auth_emp` FOREIGN KEY (`emp_id`) REFERENCES `tbl_employee_profiles` (`emp_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_auth_credentials`
--

LOCK TABLES `tbl_auth_credentials` WRITE;
/*!40000 ALTER TABLE `tbl_auth_credentials` DISABLE KEYS */;
INSERT INTO `tbl_auth_credentials` VALUES (3,'chesterd0328@gmail.com','$2b$12$NNRo4g69dgxlQMZkXz4qN.xQceSlwR4A1irO6QUI7I85USKpbdzSO',NULL,'APPROVED'),(4,'sample@mail.com','$2b$12$tp/4SE3NqWYfDuN7NYytHuRBonUyzD2pV0GCXRX4/kQ8RionaYMJq',NULL,'APPROVED'),(49,'retchair@mail.com','$2b$12$Qyg/Kvki0LKGBJGiXvpJLOIdGnTfQ6SzUKjWmywkxUSDPGnERjFGm',NULL,'APPROVED'),(50,'ret@mail.com','$2b$12$djw3aPIhOyNgBmsVl4Vv.OrRgTW/xAAtpfc.IhWa66mfa5Ew8bvCi',NULL,'APPROVED'),(51,'fac@mail.com','$2b$12$yU6KLayZ/I4G6WiGW1v1Z.oMMLS6nnvWo7.VLP3dqI76nomk9xlu2',NULL,'APPROVED'),(52,'wst@mail.com','$2b$12$sMDfHqhImC0Bo68wM3C/kOULXjFpcz1nU35QzEExhaCyCu/rY3pyS',NULL,'APPROVED'),(53,'wstfac@mail.com','$2b$12$gUL6PXRXbcRUXpUE5Om69.LW5xs.IQ4pEPIG86p5Tl7znc8npNFzS',NULL,'APPROVED'),(63,'maambensi@mail.com','$2b$12$miXgUFBVa6hPYQOIoLwnRuxv2LEJABkgVAdm.AsvnhpzD8fHtdaca',NULL,'APPROVED'),(64,'desfac@gmail.com','$2b$12$.tnQAJYbnV2eSKDKWdtI.ec34mWIzR3FnYnrHkg1IcCFYIMwSPmfS',NULL,'APPROVED'),(76,'wstprog@mail.com','$2b$12$8MIF7Dg2z/oYWZk2AGGjhunFJm05DVrhZSxXI4dO9BcWgxKk8FovW',NULL,'APPROVED'),(81,'wsttest@mail.com','$2b$12$7WZvkd6/71hjNcqjy.6w6.fpMc1WzM6gylOHQFfFbU6qQfQWw382G',NULL,'APPROVED'),(83,'test2@mail.com','$2b$12$q.jQFUlNnhSfLJ1SO3LsBu8iUM8vlwSMgU0h96UGzJFnCUSza2tvy',NULL,'APPROVED'),(86,'test3@mail.com','$2b$12$ndIni.tR9okH./2iBctiC.mkumdnFIbkSba1C1.s3XbidcUZMO4oi',NULL,'APPROVED'),(87,'test5@gmail.com','$2b$12$oED9cAli1qGKtdB3oFvhmOj/xDAAYTlge4v7GVBsnHmF4Xo5U7AqK',NULL,'APPROVED'),(88,'testf@mail.com','$2b$12$V8TBBLgv8p7WrQVWKexxNe4DbyHwm9WKvuIfALTaPlXVBRh/ihz1C',NULL,'APPROVED'),(90,'reg@mail.com','$2b$12$LLLlGakDMJQ9UVv1PpKP1eRgMFULkRSmya1M8paJRhjAlu89g3vZC',NULL,'APPROVED'),(91,'test10@gmail.com','$2b$12$O6wOhD0tatpBrbsMIBpNDuvY79qZp/dVDCz2jCquh6yWJq6a0O6wi',NULL,'APPROVED'),(92,'test11@gmail.com','$2b$12$HEZsmP/nsq.I3QdArVvcn.KanWkNFJmbp0O2DsQ.tBo/knVrLPv0K',NULL,'APPROVED'),(94,'designated@mail.com','$2b$12$EBRT34aDZTWnpWFuTrHNSufrNV4sKELykEuHTLE9xXNe2Xj.Jv4TG',NULL,'APPROVED');
/*!40000 ALTER TABLE `tbl_auth_credentials` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_cascaded_quotas`
--

DROP TABLE IF EXISTS `tbl_cascaded_quotas`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_cascaded_quotas` (
  `quota_id` int NOT NULL AUTO_INCREMENT,
  `term_id` int NOT NULL,
  `indicator_id` int NOT NULL,
  `total_target_value` int NOT NULL,
  `assigned_to_role` varchar(50) NOT NULL,
  PRIMARY KEY (`quota_id`),
  KEY `fk_quota_term` (`term_id`),
  KEY `fk_quota_ind` (`indicator_id`),
  CONSTRAINT `fk_quota_ind` FOREIGN KEY (`indicator_id`) REFERENCES `tbl_master_indicators` (`indicator_id`),
  CONSTRAINT `fk_quota_term` FOREIGN KEY (`term_id`) REFERENCES `tbl_academic_terms` (`term_id`)
) ENGINE=InnoDB AUTO_INCREMENT=153 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_cascaded_quotas`
--

LOCK TABLES `tbl_cascaded_quotas` WRITE;
/*!40000 ALTER TABLE `tbl_cascaded_quotas` DISABLE KEYS */;
INSERT INTO `tbl_cascaded_quotas` VALUES (26,3,3,3,'WST Program'),(27,3,3,4,'DST Program'),(28,3,7,7,'RET / Extension'),(29,3,10,6,'RET / Extension'),(30,3,11,9,'RET / Extension'),(31,3,9,5,'RET / Extension'),(32,3,8,5,'WST Program'),(33,3,8,5,'DST Program'),(34,4,12,2,'WST Program'),(35,4,12,2,'DST Program'),(36,4,13,2,'WST Program'),(37,4,13,2,'DST Program'),(38,4,14,2,'RET / Extension'),(39,4,15,2,'RET / Extension'),(40,4,16,2,'RET / Extension'),(41,4,17,2,'RET / Extension'),(42,4,18,2,'WST Program'),(43,4,18,2,'DST Program'),(44,4,19,2,'WST Program'),(45,4,19,2,'DST Program'),(46,4,14,1,'Instructor I'),(47,4,15,1,'Instructor I'),(51,5,21,2,'WST Program'),(52,5,22,2,'WST Program'),(53,5,29,2,'WST Program'),(54,5,23,1,'RET / Extension'),(55,5,24,1,'RET / Extension'),(56,5,25,1,'RET / Extension'),(57,5,26,1,'RET / Extension'),(58,5,27,2,'WST Program'),(59,5,28,2,'WST Program'),(60,5,23,2,'Associate Professor II'),(61,5,24,2,'Associate Professor II'),(62,5,25,2,'Associate Professor II'),(63,5,26,2,'Associate Professor II'),(64,5,23,1,'Instructor I'),(65,5,25,1,'Instructor I'),(114,6,30,1,'WST Program'),(115,6,31,1,'WST Program'),(116,6,38,1,'WST Program'),(117,6,32,1,'WST Program'),(118,6,32,1,'RET / Extension'),(119,6,33,1,'WST Program'),(120,6,33,1,'RET / Extension'),(121,6,34,1,'WST Program'),(122,6,34,1,'RET / Extension'),(123,6,35,1,'WST Program'),(124,6,35,1,'RET / Extension'),(125,6,36,1,'WST Program'),(126,6,37,1,'WST Program'),(131,6,32,1,'Instructor I'),(132,6,33,1,'Instructor I'),(133,6,34,1,'Instructor I'),(134,6,35,1,'Instructor I'),(135,7,39,4,'WST Program'),(136,7,40,4,'WST Program'),(137,7,47,4,'WST Program'),(138,7,41,1,'RET / Extension'),(139,7,42,1,'RET / Extension'),(140,7,43,1,'RET / Extension'),(141,7,44,1,'RET / Extension'),(142,7,45,4,'WST Program'),(143,7,46,4,'WST Program'),(144,8,50,2,'WST Program'),(145,8,51,2,'WST Program'),(146,8,58,2,'WST Program'),(147,8,52,2,'RET / Extension'),(148,8,53,2,'RET / Extension'),(149,8,54,2,'RET / Extension'),(150,8,55,2,'RET / Extension'),(151,8,56,2,'WST Program'),(152,8,57,2,'WST Program');
/*!40000 ALTER TABLE `tbl_cascaded_quotas` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_co_authors`
--

DROP TABLE IF EXISTS `tbl_co_authors`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_co_authors` (
  `co_author_id` int NOT NULL AUTO_INCREMENT,
  `evidence_id` int NOT NULL,
  `emp_id` int NOT NULL,
  PRIMARY KEY (`co_author_id`),
  KEY `fk_coauth_evid` (`evidence_id`),
  KEY `idx_coauth_loose_emp` (`emp_id`),
  CONSTRAINT `fk_coauth_evid` FOREIGN KEY (`evidence_id`) REFERENCES `tbl_evidence_repo` (`evidence_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_co_authors`
--

LOCK TABLES `tbl_co_authors` WRITE;
/*!40000 ALTER TABLE `tbl_co_authors` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_co_authors` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_committed_targets`
--

DROP TABLE IF EXISTS `tbl_committed_targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_committed_targets` (
  `target_id` int NOT NULL AUTO_INCREMENT,
  `emp_id` int NOT NULL,
  `indicator_id` int NOT NULL,
  `assigned_quantity` int NOT NULL,
  `status` varchar(50) DEFAULT 'Draft',
  PRIMARY KEY (`target_id`),
  KEY `fk_target_emp` (`emp_id`),
  KEY `fk_target_ind` (`indicator_id`),
  CONSTRAINT `fk_target_emp` FOREIGN KEY (`emp_id`) REFERENCES `tbl_employee_profiles` (`emp_id`),
  CONSTRAINT `fk_target_ind` FOREIGN KEY (`indicator_id`) REFERENCES `tbl_master_indicators` (`indicator_id`)
) ENGINE=InnoDB AUTO_INCREMENT=120 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_committed_targets`
--

LOCK TABLES `tbl_committed_targets` WRITE;
/*!40000 ALTER TABLE `tbl_committed_targets` DISABLE KEYS */;
INSERT INTO `tbl_committed_targets` VALUES (1,4,12,1,'Draft'),(2,52,12,1,'Draft'),(3,4,13,1,'Draft'),(4,52,13,1,'Draft'),(5,4,18,1,'Draft'),(6,52,18,1,'Draft'),(7,4,19,1,'Draft'),(8,52,19,1,'Draft'),(9,53,12,1,'Draft'),(10,53,13,1,'Draft'),(11,53,19,1,'Draft'),(12,53,18,1,'Draft'),(13,3,12,1,'Draft'),(15,49,12,1,'Draft'),(16,50,12,1,'Draft'),(17,51,12,1,'Draft'),(18,4,21,1,'Draft'),(19,52,21,1,'Draft'),(20,53,21,1,'Draft'),(21,63,21,1,'Draft'),(22,4,22,1,'Draft'),(23,52,22,1,'Draft'),(24,53,22,1,'Draft'),(25,63,22,1,'Draft'),(26,4,29,1,'Draft'),(27,52,29,1,'Draft'),(28,53,29,1,'Draft'),(29,63,29,1,'Draft'),(30,4,27,1,'Draft'),(31,52,27,1,'Draft'),(32,53,27,1,'Draft'),(33,63,27,1,'Draft'),(34,4,28,1,'Draft'),(35,52,28,1,'Draft'),(36,53,28,1,'Draft'),(37,63,28,1,'Draft'),(38,3,21,5,'Pending Approval'),(39,4,30,1,'Draft'),(40,52,30,1,'Draft'),(41,53,30,1,'Pending Approval'),(42,63,30,1,'Draft'),(43,4,31,1,'Draft'),(44,52,31,1,'Draft'),(45,53,31,1,'Pending Approval'),(46,63,31,1,'Draft'),(47,4,38,1,'Draft'),(48,52,38,1,'Draft'),(49,53,38,1,'Pending Approval'),(50,63,38,1,'Draft'),(51,4,36,1,'Draft'),(52,52,36,1,'Draft'),(53,53,36,1,'Pending Approval'),(54,63,36,1,'Draft'),(55,4,37,1,'Draft'),(56,52,37,1,'Draft'),(57,53,37,1,'Pending Approval'),(58,63,37,1,'Draft'),(59,53,32,1,'Pending Approval'),(60,53,35,1,'Pending Approval'),(61,3,30,5,'Pending Approval'),(64,53,39,2,'Approved'),(65,53,40,3,'Approved'),(66,53,47,1,'Approved'),(67,53,45,1,'Approved'),(68,53,46,1,'Approved'),(69,53,41,1,'Approved'),(70,53,43,1,'Approved'),(78,81,39,1,'Approved'),(79,81,40,1,'Approved'),(80,81,47,1,'Approved'),(81,81,45,1,'Approved'),(82,81,46,1,'Approved'),(83,81,41,4,'Approved'),(84,81,43,3,'Approved'),(85,83,39,1,'Approved'),(86,83,40,1,'Approved'),(87,83,47,1,'Approved'),(88,83,45,1,'Approved'),(89,83,46,1,'Approved'),(90,83,42,2,'Approved'),(91,83,44,5,'Approved'),(92,87,39,2,'Approved'),(93,87,40,1,'Approved'),(94,87,47,1,'Approved'),(95,87,45,2,'Approved'),(96,87,46,1,'Approved'),(97,87,41,4,'Approved'),(98,87,44,5,'Approved'),(99,88,39,4,'Approved'),(100,88,40,2,'Approved'),(101,88,47,1,'Approved'),(102,88,45,1,'Approved'),(103,88,46,1,'Approved'),(104,88,41,4,'Approved'),(105,88,44,5,'Approved'),(106,91,39,3,'Approved'),(107,91,40,1,'Approved'),(108,91,47,1,'Approved'),(109,91,45,2,'Approved'),(110,91,46,1,'Approved'),(111,91,41,4,'Approved'),(112,91,43,3,'Approved'),(113,92,39,3,'Approved'),(114,92,40,2,'Approved'),(115,92,47,1,'Approved'),(116,92,45,2,'Approved'),(117,92,46,2,'Approved'),(118,92,42,2,'Approved'),(119,92,44,5,'Approved');
/*!40000 ALTER TABLE `tbl_committed_targets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_designation_targets`
--

DROP TABLE IF EXISTS `tbl_designation_targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_designation_targets` (
  `template_id` int NOT NULL AUTO_INCREMENT,
  `designation_role` varchar(50) NOT NULL,
  `indicator_id` int NOT NULL,
  PRIMARY KEY (`template_id`),
  KEY `fk_destarget_ind` (`indicator_id`),
  CONSTRAINT `fk_destarget_ind` FOREIGN KEY (`indicator_id`) REFERENCES `tbl_master_indicators` (`indicator_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_designation_targets`
--

LOCK TABLES `tbl_designation_targets` WRITE;
/*!40000 ALTER TABLE `tbl_designation_targets` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_designation_targets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_draft_allocation`
--

DROP TABLE IF EXISTS `tbl_draft_allocation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_draft_allocation` (
  `allocation_id` int NOT NULL AUTO_INCREMENT,
  `emp_id` int NOT NULL,
  `indicator_id` int NOT NULL,
  `assigned_quantity` int NOT NULL,
  PRIMARY KEY (`allocation_id`),
  KEY `fk_draftalloc_emp` (`emp_id`),
  KEY `fk_draftalloc_ind` (`indicator_id`),
  CONSTRAINT `fk_draftalloc_emp` FOREIGN KEY (`emp_id`) REFERENCES `tbl_employee_profiles` (`emp_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_draftalloc_ind` FOREIGN KEY (`indicator_id`) REFERENCES `tbl_master_indicators` (`indicator_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_draft_allocation`
--

LOCK TABLES `tbl_draft_allocation` WRITE;
/*!40000 ALTER TABLE `tbl_draft_allocation` DISABLE KEYS */;
INSERT INTO `tbl_draft_allocation` VALUES (3,4,39,1),(4,52,39,1),(6,63,39,1),(7,64,39,1),(8,4,40,1),(9,52,40,1),(11,63,40,1),(12,64,40,1),(13,4,47,1),(14,52,47,1),(16,63,47,1),(17,64,47,1),(18,4,45,1),(19,52,45,1),(21,63,45,1),(22,64,45,1),(23,4,46,1),(24,52,46,1),(26,63,46,1),(27,64,46,1);
/*!40000 ALTER TABLE `tbl_draft_allocation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_draft_targets`
--

DROP TABLE IF EXISTS `tbl_draft_targets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_draft_targets` (
  `draft_id` int NOT NULL AUTO_INCREMENT,
  `emp_id` int NOT NULL,
  `indicator_id` int NOT NULL,
  `proposed_quantity` int NOT NULL,
  `review_status` varchar(50) DEFAULT 'Pending Review' COMMENT 'Pending Review, Returned, or Approved',
  `manager_feedback` text,
  PRIMARY KEY (`draft_id`),
  KEY `fk_drafttarget_emp` (`emp_id`),
  KEY `fk_drafttarget_ind` (`indicator_id`),
  CONSTRAINT `fk_drafttarget_emp` FOREIGN KEY (`emp_id`) REFERENCES `tbl_employee_profiles` (`emp_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_drafttarget_ind` FOREIGN KEY (`indicator_id`) REFERENCES `tbl_master_indicators` (`indicator_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=155 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_draft_targets`
--

LOCK TABLES `tbl_draft_targets` WRITE;
/*!40000 ALTER TABLE `tbl_draft_targets` DISABLE KEYS */;
INSERT INTO `tbl_draft_targets` VALUES (4,53,39,1,'Pending Review',NULL),(5,53,40,1,'Pending Review',NULL),(6,53,47,1,'Pending Review',NULL),(7,53,45,1,'Pending Review',NULL),(8,53,46,1,'Pending Review',NULL),(25,81,39,1,'Approved',NULL),(26,81,40,1,'Approved',NULL),(27,81,47,1,'Approved',NULL),(28,81,45,1,'Approved',NULL),(29,81,46,1,'Approved',NULL),(40,53,41,4,'Pending Review',NULL),(41,53,43,3,'Pending Review',NULL),(46,81,41,4,'Approved',NULL),(47,81,43,3,'Approved',NULL),(48,83,39,1,'Approved',NULL),(49,83,40,1,'Approved',NULL),(50,83,47,1,'Approved',NULL),(51,83,45,1,'Approved',NULL),(52,83,46,1,'Approved',NULL),(58,83,42,2,'Approved',NULL),(59,83,44,5,'Approved',NULL),(99,86,39,1,'Waiting for Approval',NULL),(100,86,40,1,'Waiting for Approval',NULL),(101,86,47,1,'Waiting for Approval',NULL),(102,86,45,1,'Waiting for Approval',NULL),(103,86,46,1,'Waiting for Approval',NULL),(104,86,41,4,'Waiting for Approval',NULL),(105,86,43,3,'Waiting for Approval',NULL),(106,87,39,2,'Approved',NULL),(107,87,40,1,'Approved',NULL),(108,87,47,1,'Approved',NULL),(109,87,45,2,'Approved',NULL),(110,87,46,1,'Approved',NULL),(113,87,41,4,'Approved',NULL),(114,87,44,5,'Approved',NULL),(115,88,39,4,'Approved',NULL),(116,88,40,2,'Approved',NULL),(117,88,47,1,'Approved',NULL),(118,88,45,1,'Approved',NULL),(119,88,46,1,'Approved',NULL),(122,88,41,4,'Approved',NULL),(123,88,44,5,'Approved',NULL),(124,90,39,1,'Pending Review',NULL),(125,90,40,1,'Pending Review',NULL),(126,90,47,1,'Pending Review',NULL),(127,90,45,1,'Pending Review',NULL),(128,90,46,1,'Pending Review',NULL),(129,90,42,2,'Pending Review',NULL),(130,90,43,3,'Pending Review',NULL),(131,91,39,3,'Approved',NULL),(132,91,40,1,'Approved',NULL),(133,91,47,1,'Approved',NULL),(134,91,45,2,'Approved',NULL),(135,91,46,1,'Approved',NULL),(138,91,41,4,'Approved',NULL),(139,91,43,3,'Approved',NULL),(140,92,39,3,'Approved',NULL),(141,92,40,2,'Approved',NULL),(142,92,47,1,'Approved',NULL),(143,92,45,2,'Approved',NULL),(144,92,46,2,'Approved',NULL),(147,92,42,2,'Approved',NULL),(148,92,44,5,'Approved',NULL);
/*!40000 ALTER TABLE `tbl_draft_targets` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_employee_profiles`
--

DROP TABLE IF EXISTS `tbl_employee_profiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_employee_profiles` (
  `emp_id` int NOT NULL AUTO_INCREMENT,
  `employee_id_number` varchar(50) NOT NULL,
  `first_name` varchar(100) NOT NULL,
  `last_name` varchar(100) NOT NULL,
  `college` varchar(100) NOT NULL DEFAULT 'CICT',
  `assigned_program` varchar(100) NOT NULL,
  `academic_rank` varchar(100) NOT NULL,
  `employment_status` varchar(50) NOT NULL,
  `designation` varchar(50) DEFAULT 'None',
  `leave_status` varchar(50) DEFAULT 'Active',
  `specialization` varchar(250) DEFAULT NULL,
  PRIMARY KEY (`emp_id`),
  UNIQUE KEY `employee_id_number` (`employee_id_number`)
) ENGINE=InnoDB AUTO_INCREMENT=95 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_employee_profiles`
--

LOCK TABLES `tbl_employee_profiles` WRITE;
/*!40000 ALTER TABLE `tbl_employee_profiles` DISABLE KEYS */;
INSERT INTO `tbl_employee_profiles` VALUES (3,'2017-1055','Chester','Dayao','CICT','BSIT','Instructor II','Regular','Admin','Active','DST Program'),(4,'2017-100055','Oks','Dayao','CICT','BSIT','Instructor II','Regular','Dean','Active','WST Program'),(49,'22222','Ivan','Fajardo','CICT','BSIT','Associate Professor III','Regular','RET Chair','Active','DST Program'),(50,'3333','Ivan','Fajardo','CICT','BSIT','Associate Professor V','Regular','Designated Faculty','Active','DST Program'),(51,'5555','Nicole ','Zefanya','CICT','BSIT','Asst. Professor I','Regular','Regular Faculty','Active','DST Program'),(52,'2222','Dayao','Chester','CICT','BSIT','Asst. Professor I','Regular','Program Chair','Active','WST Program'),(53,'999','wst','fac','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(63,'820','Maam ','Bensi','CICT','BSIT','Associate Professor II','Regular','Regular Faculty','Active','WST Program'),(64,'777','Ruka','Kayamori','CICT','BSIT','Instructor I','Regular','Designated Faculty','Active','WST Program'),(76,'2026-5555','nst','prog','CICT','BSIT','Associate Professor II','Regular','Program Chair','Active','NST Program'),(81,'2026-4441','wst','sample','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(83,'1234','wst','test2','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(86,'2026-6767','wst','test4','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(87,'555-222','wst','test5','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(88,'2026-7777','wst','finaltest','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(90,'111','Majima','Goro','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(91,'2026-8888','wst','sample10','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(92,'2026-9999','wst','test11','CICT','BSIT','Instructor I','Regular','Regular Faculty','Active','WST Program'),(94,'0975','designated','faculty','CICT','BSIT','Instructor I','Regular','Designated Faculty','Active','WST Program');
/*!40000 ALTER TABLE `tbl_employee_profiles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_evidence_repo`
--

DROP TABLE IF EXISTS `tbl_evidence_repo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_evidence_repo` (
  `evidence_id` int NOT NULL AUTO_INCREMENT,
  `target_id` int NOT NULL,
  `file_path` varchar(255) NOT NULL,
  `actual_qty_Q` int NOT NULL,
  `timeliness_T` decimal(3,2) DEFAULT NULL,
  `efficiency_rating_E` int DEFAULT NULL,
  `verification_status` varchar(50) DEFAULT 'Pending',
  `supervisor_comment` text,
  PRIMARY KEY (`evidence_id`),
  KEY `fk_evid_target` (`target_id`),
  CONSTRAINT `fk_evid_target` FOREIGN KEY (`target_id`) REFERENCES `tbl_committed_targets` (`target_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_evidence_repo`
--

LOCK TABLES `tbl_evidence_repo` WRITE;
/*!40000 ALTER TABLE `tbl_evidence_repo` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_evidence_repo` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_final_scores`
--

DROP TABLE IF EXISTS `tbl_final_scores`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_final_scores` (
  `score_id` int NOT NULL AUTO_INCREMENT,
  `emp_id` int NOT NULL,
  `term_id` int NOT NULL,
  `instruction_weighted` decimal(4,2) DEFAULT NULL,
  `ret_weighted` decimal(4,2) DEFAULT NULL,
  `support_weighted` decimal(4,2) DEFAULT NULL,
  `admin_weighted` decimal(4,2) DEFAULT NULL,
  `final_score` decimal(4,2) NOT NULL,
  `adjectival_rating` varchar(50) NOT NULL,
  `dean_approval_status` varchar(50) DEFAULT 'Pending',
  PRIMARY KEY (`score_id`),
  KEY `fk_score_emp` (`emp_id`),
  KEY `fk_score_term` (`term_id`),
  CONSTRAINT `fk_score_emp` FOREIGN KEY (`emp_id`) REFERENCES `tbl_employee_profiles` (`emp_id`),
  CONSTRAINT `fk_score_term` FOREIGN KEY (`term_id`) REFERENCES `tbl_academic_terms` (`term_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_final_scores`
--

LOCK TABLES `tbl_final_scores` WRITE;
/*!40000 ALTER TABLE `tbl_final_scores` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_final_scores` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_ipcr_chair_review`
--

DROP TABLE IF EXISTS `tbl_ipcr_chair_review`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_ipcr_chair_review` (
  `review_id` int NOT NULL AUTO_INCREMENT,
  `emp_id` int NOT NULL,
  `term_id` int NOT NULL,
  `chair_emp_id` int NOT NULL,
  `overall_status` enum('Pending','Approved','Rejected') DEFAULT 'Pending',
  `overall_remarks` text,
  `reviewed_at` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`review_id`),
  UNIQUE KEY `uq_review` (`emp_id`,`term_id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_ipcr_chair_review`
--

LOCK TABLES `tbl_ipcr_chair_review` WRITE;
/*!40000 ALTER TABLE `tbl_ipcr_chair_review` DISABLE KEYS */;
INSERT INTO `tbl_ipcr_chair_review` VALUES (4,64,7,52,'Pending',NULL,NULL,'2026-06-22 02:30:54'),(6,46,7,46,'Pending',NULL,NULL,'2026-06-24 09:19:32'),(11,53,7,52,'Rejected','Instruction targets adjusted and returned to faculty.',NULL,'2026-06-24 11:06:18'),(14,81,7,52,'Approved','finished','2026-06-24 19:43:13','2026-06-24 11:42:38'),(17,83,7,52,'Approved','','2026-06-25 21:35:12','2026-06-25 13:33:43'),(19,86,7,52,'Pending',NULL,NULL,'2026-06-25 14:58:53'),(20,87,7,52,'Approved','finished','2026-06-25 23:19:59','2026-06-25 15:17:24'),(21,88,7,52,'Approved','','2026-06-25 23:45:44','2026-06-25 15:41:37'),(22,91,7,52,'Approved','','2026-06-27 18:11:17','2026-06-27 10:02:49'),(23,90,7,52,'Approved','','2026-06-27 18:10:31','2026-06-27 10:10:04'),(24,92,7,52,'Approved','','2026-06-27 18:46:26','2026-06-27 10:28:22');
/*!40000 ALTER TABLE `tbl_ipcr_chair_review` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_ipcr_chair_review_items`
--

DROP TABLE IF EXISTS `tbl_ipcr_chair_review_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_ipcr_chair_review_items` (
  `item_id` int NOT NULL AUTO_INCREMENT,
  `review_id` int NOT NULL,
  `draft_id` int NOT NULL,
  `indicator_id` int NOT NULL,
  `original_quantity` int NOT NULL,
  `reviewed_quantity` int NOT NULL,
  `item_remarks` varchar(1000) DEFAULT NULL,
  PRIMARY KEY (`item_id`),
  KEY `review_id` (`review_id`),
  CONSTRAINT `tbl_ipcr_chair_review_items_ibfk_1` FOREIGN KEY (`review_id`) REFERENCES `tbl_ipcr_chair_review` (`review_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=162 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_ipcr_chair_review_items`
--

LOCK TABLES `tbl_ipcr_chair_review_items` WRITE;
/*!40000 ALTER TABLE `tbl_ipcr_chair_review_items` DISABLE KEYS */;
INSERT INTO `tbl_ipcr_chair_review_items` VALUES (8,4,13,39,1,1,NULL),(9,4,14,40,0,0,NULL),(10,4,15,47,0,0,NULL),(11,4,16,45,0,0,NULL),(12,4,17,46,0,0,NULL),(13,4,18,49,1,1,NULL),(16,6,11,39,4,4,NULL),(17,6,12,48,7,7,NULL),(39,11,4,39,1,2,'Program Chair adjustment.'),(40,11,5,40,1,2,'Program Chair adjustment.'),(41,11,6,47,1,2,'Program Chair adjustment.'),(42,11,7,45,1,1,NULL),(43,11,8,46,1,1,NULL),(44,11,40,41,4,4,NULL),(45,11,41,43,3,3,NULL),(60,14,25,39,1,1,NULL),(61,14,26,40,1,1,NULL),(62,14,27,47,1,1,NULL),(63,14,28,45,1,1,NULL),(64,14,29,46,1,1,NULL),(65,14,46,41,4,4,NULL),(66,14,47,43,3,3,NULL),(81,17,48,39,1,1,NULL),(82,17,49,40,1,1,NULL),(83,17,50,47,1,1,NULL),(84,17,51,45,1,1,NULL),(85,17,52,46,1,1,NULL),(86,17,58,42,2,2,NULL),(87,17,59,44,5,5,NULL),(102,19,92,39,1,1,NULL),(103,19,93,40,1,1,NULL),(104,19,94,47,1,1,NULL),(105,19,95,45,1,1,NULL),(106,19,96,46,1,1,NULL),(109,19,99,39,1,1,NULL),(110,19,100,40,1,1,NULL),(111,19,101,47,1,1,NULL),(112,19,102,45,1,1,NULL),(113,19,103,46,1,1,NULL),(114,19,104,41,4,4,NULL),(115,19,105,43,3,3,NULL),(116,20,106,39,1,2,'aaa'),(117,20,107,40,1,1,NULL),(118,20,108,47,1,1,NULL),(119,20,109,45,1,2,'ddd'),(120,20,110,46,1,1,NULL),(123,20,113,41,4,4,NULL),(124,20,114,44,5,5,NULL),(126,21,115,39,1,4,'aaa'),(127,21,116,40,1,2,'cvvv'),(128,21,117,47,1,1,NULL),(129,21,118,45,1,1,NULL),(130,21,119,46,1,1,NULL),(133,21,122,41,4,4,NULL),(134,21,123,44,5,5,NULL),(136,22,131,39,1,3,'test remarks'),(137,22,132,40,1,1,NULL),(138,22,133,47,1,1,NULL),(139,22,134,45,1,2,'trest'),(140,22,135,46,1,1,NULL),(143,22,138,41,4,4,NULL),(144,22,139,43,3,3,NULL),(146,23,124,39,1,1,NULL),(147,23,125,40,1,1,NULL),(148,23,126,47,1,1,NULL),(149,23,127,45,1,1,NULL),(150,23,128,46,1,1,NULL),(151,23,129,42,2,2,NULL),(152,23,130,43,3,3,NULL),(153,24,140,39,1,3,'test 1'),(154,24,141,40,1,2,'test 2'),(155,24,142,47,1,1,NULL),(156,24,143,45,1,2,'a'),(157,24,144,46,1,2,'a'),(160,24,147,42,2,2,NULL),(161,24,148,44,5,5,NULL);
/*!40000 ALTER TABLE `tbl_ipcr_chair_review_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_ipcr_dean_review`
--

DROP TABLE IF EXISTS `tbl_ipcr_dean_review`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_ipcr_dean_review` (
  `review_id` int NOT NULL AUTO_INCREMENT,
  `emp_id` int NOT NULL,
  `term_id` int NOT NULL,
  `dean_id` int NOT NULL,
  `overall_status` varchar(20) DEFAULT 'Pending',
  `overall_remarks` text,
  `reviewed_at` datetime DEFAULT NULL,
  PRIMARY KEY (`review_id`)
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_ipcr_dean_review`
--

LOCK TABLES `tbl_ipcr_dean_review` WRITE;
/*!40000 ALTER TABLE `tbl_ipcr_dean_review` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_ipcr_dean_review` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_ipcr_dean_review_items`
--

DROP TABLE IF EXISTS `tbl_ipcr_dean_review_items`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_ipcr_dean_review_items` (
  `item_id` int NOT NULL AUTO_INCREMENT,
  `review_id` int NOT NULL,
  `draft_id` int DEFAULT NULL,
  `indicator_id` int NOT NULL,
  `original_quantity` int DEFAULT '0',
  `reviewed_quantity` int DEFAULT '0',
  `item_remarks` text,
  PRIMARY KEY (`item_id`)
) ENGINE=InnoDB AUTO_INCREMENT=50 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_ipcr_dean_review_items`
--

LOCK TABLES `tbl_ipcr_dean_review_items` WRITE;
/*!40000 ALTER TABLE `tbl_ipcr_dean_review_items` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_ipcr_dean_review_items` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_master_indicators`
--

DROP TABLE IF EXISTS `tbl_master_indicators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_master_indicators` (
  `indicator_id` int NOT NULL AUTO_INCREMENT,
  `category_id` int NOT NULL,
  `indicator_description` text NOT NULL,
  `efficiency_type` varchar(50) NOT NULL,
  `term_id` int DEFAULT NULL,
  `is_custom` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`indicator_id`),
  KEY `fk_master_cat` (`category_id`),
  CONSTRAINT `fk_master_cat` FOREIGN KEY (`category_id`) REFERENCES `tbl_target_categories` (`category_id`)
) ENGINE=InnoDB AUTO_INCREMENT=60 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_master_indicators`
--

LOCK TABLES `tbl_master_indicators` WRITE;
/*!40000 ALTER TABLE `tbl_master_indicators` DISABLE KEYS */;
INSERT INTO `tbl_master_indicators` VALUES (1,1,'Sample Indicator 1 - 21HRS OF TEACHING','Quantity-Based',2,0),(3,1,'Sample Indicator 1 - 21HRS OF TEACHING','Quantity-Based',3,0),(7,2,'sample research','Quantity-Based',3,0),(8,4,'Sample 2','Quantity-Based',3,0),(9,3,'Sample Extension 1','Quantity-Based',3,0),(10,2,'research sample 3','Quantity-Based',3,0),(11,2,'sample research 4','Quantity-Based',3,0),(12,1,'INSTRUCT 1','Quantity-Based',4,0),(13,1,'INSTRUCT 2','Quantity-Based',4,0),(14,2,'RESA 1\r\n','Quantity-Based',4,0),(15,2,'RESA 2','Quantity-Based',4,0),(16,3,'EXT 1','Quantity-Based',4,0),(17,3,'EXT 2','Quantity-Based',4,0),(18,4,'SUP 1','Quantity-Based',4,0),(19,4,'SUP 2','Quantity-Based',4,0),(20,1,'INSTRUCT 3','Quantity-Based',4,0),(21,1,'INSTRUCT 1','Quantity-Based',5,0),(22,1,'INSTRUCT 2','Quantity-Based',5,0),(23,2,'RESA 1\r\n','Quantity-Based',5,0),(24,2,'RESA 2','Quantity-Based',5,0),(25,3,'EXT 1','Quantity-Based',5,0),(26,3,'EXT 2','Quantity-Based',5,0),(27,4,'SUP 1','Quantity-Based',5,0),(28,4,'SUP 2','Quantity-Based',5,0),(29,1,'INSTRUCT 3','Quantity-Based',5,0),(30,1,'INSTRUCT 1','Quantity-Based',6,0),(31,1,'INSTRUCT 2','Quantity-Based',6,0),(32,2,'RESA 1\r\n','Quantity-Based',6,0),(33,2,'RESA 2','Quantity-Based',6,0),(34,3,'EXT 1','Quantity-Based',6,0),(35,3,'EXT 2','Quantity-Based',6,0),(36,4,'SUP 1','Quantity-Based',6,0),(37,4,'SUP 2','Quantity-Based',6,0),(38,1,'INSTRUCT 3','Quantity-Based',6,0),(39,1,'INSTRUCT 1','Quantity-Based',7,0),(40,1,'INSTRUCT 2','Quantity-Based',7,0),(41,2,'RESA 1\r\n','Quantity-Based',7,0),(42,2,'RESA 2','Quantity-Based',7,0),(43,3,'EXT 1','Quantity-Based',7,0),(44,3,'EXT 2','Quantity-Based',7,0),(45,4,'SUP 1','Quantity-Based',7,0),(46,4,'SUP 2','Quantity-Based',7,0),(47,1,'INSTRUCT 3','Quantity-Based',7,0),(48,5,'MOCK CUSTOM DESIGNATED TARGET FOR TESTING','Output-Based',7,1),(49,5,'ADMIN 1','Output-Based',7,1),(50,1,'INSTRUCT 1','Quantity-Based',8,0),(51,1,'INSTRUCT 2','Quantity-Based',8,0),(52,2,'RESA 1\r\n','Quantity-Based',8,0),(53,2,'RESA 2','Quantity-Based',8,0),(54,3,'EXT 1','Quantity-Based',8,0),(55,3,'EXT 2','Quantity-Based',8,0),(56,4,'SUP 1','Quantity-Based',8,0),(57,4,'SUP 2','Quantity-Based',8,0),(58,1,'INSTRUCT 3','Quantity-Based',8,0),(59,5,'CUS 1','Output-Based',8,1);
/*!40000 ALTER TABLE `tbl_master_indicators` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_research_options`
--

DROP TABLE IF EXISTS `tbl_research_options`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_research_options` (
  `option_id` int NOT NULL AUTO_INCREMENT,
  `term_id` int NOT NULL,
  `academic_rank` varchar(100) NOT NULL,
  `indicator_id` int NOT NULL,
  PRIMARY KEY (`option_id`),
  KEY `fk_opt_term` (`term_id`),
  KEY `fk_opt_indicator` (`indicator_id`),
  CONSTRAINT `fk_opt_indicator` FOREIGN KEY (`indicator_id`) REFERENCES `tbl_master_indicators` (`indicator_id`) ON DELETE CASCADE,
  CONSTRAINT `fk_opt_term` FOREIGN KEY (`term_id`) REFERENCES `tbl_academic_terms` (`term_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_research_options`
--

LOCK TABLES `tbl_research_options` WRITE;
/*!40000 ALTER TABLE `tbl_research_options` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_research_options` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_research_requirements`
--

DROP TABLE IF EXISTS `tbl_research_requirements`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_research_requirements` (
  `req_id` int NOT NULL AUTO_INCREMENT,
  `term_id` int NOT NULL,
  `academic_rank` varchar(100) NOT NULL,
  `required_selections` int NOT NULL DEFAULT '1',
  PRIMARY KEY (`req_id`),
  KEY `fk_req_term` (`term_id`),
  CONSTRAINT `fk_req_term` FOREIGN KEY (`term_id`) REFERENCES `tbl_academic_terms` (`term_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_research_requirements`
--

LOCK TABLES `tbl_research_requirements` WRITE;
/*!40000 ALTER TABLE `tbl_research_requirements` DISABLE KEYS */;
/*!40000 ALTER TABLE `tbl_research_requirements` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_ret_rule_indicators`
--

DROP TABLE IF EXISTS `tbl_ret_rule_indicators`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_ret_rule_indicators` (
  `rule_indicator_id` int NOT NULL AUTO_INCREMENT,
  `rule_id` int NOT NULL,
  `indicator_id` int NOT NULL,
  `target_quantity` int DEFAULT '1',
  PRIMARY KEY (`rule_indicator_id`),
  KEY `rule_id` (`rule_id`),
  KEY `indicator_id` (`indicator_id`),
  CONSTRAINT `tbl_ret_rule_indicators_ibfk_1` FOREIGN KEY (`rule_id`) REFERENCES `tbl_ret_rules` (`rule_id`) ON DELETE CASCADE,
  CONSTRAINT `tbl_ret_rule_indicators_ibfk_2` FOREIGN KEY (`indicator_id`) REFERENCES `tbl_master_indicators` (`indicator_id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_ret_rule_indicators`
--

LOCK TABLES `tbl_ret_rule_indicators` WRITE;
/*!40000 ALTER TABLE `tbl_ret_rule_indicators` DISABLE KEYS */;
INSERT INTO `tbl_ret_rule_indicators` VALUES (9,5,41,4),(10,5,42,2),(11,6,43,3),(12,6,44,5);
/*!40000 ALTER TABLE `tbl_ret_rule_indicators` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_ret_rules`
--

DROP TABLE IF EXISTS `tbl_ret_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_ret_rules` (
  `rule_id` int NOT NULL AUTO_INCREMENT,
  `academic_rank` varchar(255) NOT NULL,
  `required_selections` int NOT NULL,
  PRIMARY KEY (`rule_id`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_ret_rules`
--

LOCK TABLES `tbl_ret_rules` WRITE;
/*!40000 ALTER TABLE `tbl_ret_rules` DISABLE KEYS */;
INSERT INTO `tbl_ret_rules` VALUES (5,'Instructor I',1),(6,'Instructor I',1);
/*!40000 ALTER TABLE `tbl_ret_rules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_system_access`
--

DROP TABLE IF EXISTS `tbl_system_access`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_system_access` (
  `emp_id` int NOT NULL,
  `system_role` varchar(50) NOT NULL,
  `account_status` varchar(50) DEFAULT 'Pending',
  PRIMARY KEY (`emp_id`),
  CONSTRAINT `fk_access_emp` FOREIGN KEY (`emp_id`) REFERENCES `tbl_employee_profiles` (`emp_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_system_access`
--

LOCK TABLES `tbl_system_access` WRITE;
/*!40000 ALTER TABLE `tbl_system_access` DISABLE KEYS */;
INSERT INTO `tbl_system_access` VALUES (3,'Admin','Active'),(4,'DEAN','Active'),(49,'RET_CHAIR','Active'),(50,'DESIGNATED_FACULTY','Active'),(51,'FACULTY','Active'),(52,'PROGRAM_CHAIR','Active'),(53,'FACULTY','Active'),(63,'FACULTY','Active'),(64,'DESIGNATED_FACULTY','Approved'),(76,'FACULTY','Inactive'),(81,'FACULTY','Active'),(83,'FACULTY','Active'),(86,'FACULTY','Active'),(87,'FACULTY','Active'),(88,'FACULTY','Active'),(90,'FACULTY','Active'),(91,'FACULTY','Active'),(92,'FACULTY','Active'),(94,'DESIGNATED_FACULTY','Active');
/*!40000 ALTER TABLE `tbl_system_access` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tbl_target_categories`
--

DROP TABLE IF EXISTS `tbl_target_categories`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tbl_target_categories` (
  `category_id` int NOT NULL AUTO_INCREMENT,
  `category_name` varchar(100) NOT NULL,
  PRIMARY KEY (`category_id`),
  UNIQUE KEY `category_name` (`category_name`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tbl_target_categories`
--

LOCK TABLES `tbl_target_categories` WRITE;
/*!40000 ALTER TABLE `tbl_target_categories` DISABLE KEYS */;
INSERT INTO `tbl_target_categories` VALUES (1,'A. Instructions'),(2,'A. Research'),(3,'B. Extension Services / Training / Advisory'),(5,'Custom Target Items'),(4,'Support Functions');
/*!40000 ALTER TABLE `tbl_target_categories` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'ipcr_db'
--

-- insufficient privileges to SHOW CREATE PROCEDURE `get_user_by_email`
-- does app_user have permissions on mysql.proc?

